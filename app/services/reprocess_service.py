"""
Re-processing: any edit to a student profile, diagnostic score, course or academic rule immediately
re-runs the deterministic pipeline (skill state -> gaps -> planner -> validator) and stores a new
roadmap version with a PlanDiff and the reason.

Two entry points
  * API edits (Admin UI)      -> synchronous: the HTTP response already contains the new version + diff.
  * Direct SQL / Adminer edits -> PostgreSQL triggers write ops.reprocess_queue; a background worker
                                  polls the queue (every 2 s), reloads the changed rows from the database
                                  and re-plans. No LLM is involved anywhere in this path.
"""
import os
import sys
import time
import logging
import threading
import subprocess
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service
from app.services.plan_service import plan_service
from app.db import persistence

logger = logging.getLogger("ebuddy.reprocess")
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class ReprocessService:
    def __init__(self):
        self.log: deque = deque(maxlen=60)
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.RLock()
        self.poll_seconds = float(os.getenv("REPROCESS_POLL_SECONDS", "2"))

    def _record(self, kind: str, target: str, detail: str, source: str, result: Optional[Dict[str, Any]] = None):
        entry = {"at": datetime.now(timezone.utc).isoformat(), "kind": kind, "target": target, "detail": detail, "source": source}
        if result:
            entry.update(result)
        self.log.appendleft(entry)
        return entry

    # ------------------------------------------------------------------ student
    def reprocess_student(self, student_id: str, reason: str, trigger: str = "admin_edit", reload_from_db: bool = False,
                          source: str = "api") -> Dict[str, Any]:
        with self._lock:
            if reload_from_db:
                bundle = persistence.fetch_student_bundle(student_id)
                if bundle:
                    onboarding_service.load_from_bundle(bundle)
            if student_id not in onboarding_service.students:
                onboarding_service.ensure_student_onboarded(student_id)
            before = plan_service.get_plan(student_id)
            res = plan_service.create_or_update_plan(student_id, trigger=trigger, reasons=[reason])
            after = plan_service.get_plan(student_id)
            out = {
                "student_id": student_id, "old_version": before.version if before else 0, "new_version": after.version,
                "summary": after.plan_diff.summary if after.plan_diff else "",
                "validation_passed": bool(after.validation_report.passed) if after.validation_report else None,
            }
            self._record("student", student_id, reason, source, out)
            return {**out, "plan_diff": res["plan_diff"], "what_changed_and_why": res["what_changed_and_why"],
                    "validation": res["validation"], "reason": reason, "status": "reprocessed"}

    # ------------------------------------------------------------------ knowledge base
    def _course_singletons(self):
        repos = [plan_service.agent_1.course_repo]
        try:
            from app.api import ui_routes
            repos.append(ui_routes.course_repo)
        except Exception:
            pass
        try:
            from app.services.chat_service import chat_service
            repos.append(chat_service.course_repo)
        except Exception:
            pass
        return repos

    def apply_course_update(self, course_id: str, fields: Dict[str, Any], source: str = "api") -> Dict[str, Any]:
        """Applies an edited course (credits / title) to every in-memory KB view and re-plans affected students."""
        with self._lock:
            planner, validator = plan_service.planner, plan_service.validator
            if course_id not in planner.course_info:
                raise ValueError(f"Course {course_id} is not in the knowledge base.")
            old = dict(planner.course_info[course_id])
            changes = {}
            if fields.get("credits") is not None and float(fields["credits"]) != float(old["credits"]):
                changes["credits"] = [old["credits"], float(fields["credits"])]
                planner.course_info[course_id]["credits"] = float(fields["credits"])
                validator.valid_courses[course_id]["credits"] = float(fields["credits"])
            if fields.get("title") and fields["title"] != old["title"]:
                changes["title"] = [old["title"], fields["title"]]
                planner.course_info[course_id]["title"] = fields["title"]
                validator.valid_courses[course_id]["title"] = fields["title"]
            for repo in self._course_singletons():
                c = repo._courses.get(course_id)
                if c is not None:
                    upd = {}
                    if "credits" in changes:
                        upd["credits"] = changes["credits"][1]
                    if "title" in changes:
                        upd["title"] = changes["title"][1]
                    if upd:
                        repo._courses[course_id] = c.model_copy(update=upd)
            affected = []
            if changes:
                desc = "; ".join(f"{k}: {v[0]} -> {v[1]}" for k, v in changes.items())
                reason = f"Course data edited: {course_id} ({desc}). Credit loads, caps and weekly hours were recomputed."
                for sid, plan in list(plan_service.plans.items()):
                    if any(it.course_id == course_id for it in plan.items) or course_id in onboarding_service.completed_courses.get(sid, []):
                        affected.append(self.reprocess_student(sid, reason, trigger="course_edit", source=source))
            self._record("course", course_id, str(changes) if changes else "no effective change", source,
                         {"students_reprocessed": len(affected)})
            return {"course_id": course_id, "changes": changes, "students_reprocessed": len(affected),
                    "affected": [{k: a[k] for k in ("student_id", "old_version", "new_version", "summary", "validation_passed")} for a in affected]}

    def apply_rule_update(self, rule_id: str, parameters: Dict[str, Any], source: str = "api") -> Dict[str, Any]:
        with self._lock:
            planner, validator = plan_service.planner, plan_service.validator
            if rule_id not in validator.academic_rules:
                raise ValueError(f"Rule {rule_id} is not in the knowledge base.")
            old = dict(validator.academic_rules[rule_id].get("parameters", {}))
            merged = {**old, **parameters}
            validator.academic_rules[rule_id]["parameters"] = merged
            planner.rule_engine._rule_params(rule_id)  # make sure the cache exists
            planner.rule_engine._rules_cache[rule_id] = merged
            reason = f"Academic rule edited: {rule_id} parameters {old} -> {merged}."
            affected = [self.reprocess_student(sid, reason, trigger="rule_edit", source=source) for sid in list(plan_service.plans)]
            self._record("rule", rule_id, f"{old} -> {merged}", source, {"students_reprocessed": len(affected)})
            return {"rule_id": rule_id, "old_parameters": old, "new_parameters": merged, "students_reprocessed": len(affected),
                    "affected": [{k: a[k] for k in ("student_id", "old_version", "new_version", "summary", "validation_passed")} for a in affected]}

    # ------------------------------------------------------------------ reset
    def reset_memory(self, source: str = "api"):
        """Restores the in-memory state to the seed: students, evidence, plans, proposals and KB overlays."""
        with self._lock:
            onboarding_service.reset()
            diagnostic_service.clear_all()
            plan_service.reset()
            plan_service.planner._load_knowledge_base()
            plan_service.validator._load_knowledge_base()
            if hasattr(plan_service.planner.rule_engine, "_rules_cache"):
                del plan_service.planner.rule_engine._rules_cache
            plan_service._load_requirements()
            for repo in self._course_singletons():
                repo._courses.clear()
                repo._load()
            try:
                from app.services.roadmap_orchestrator import roadmap_orchestrator
                roadmap_orchestrator.reset()
            except Exception:
                pass
            self._record("system", "ALL", "in-memory state restored to seed", source)

    def reset_all(self) -> Dict[str, Any]:
        """Full reset: reloads the PostgreSQL seed (if reachable) and restores the in-memory state."""
        db = {"attempted": False, "ok": False, "detail": "database not reachable; in-memory state restored from seed files"}
        if persistence.db_available(ttl=0):
            db["attempted"] = True
            try:
                proc = subprocess.run([sys.executable, os.path.join(_REPO_ROOT, "scripts", "seed_loader.py"), "--reset"],
                                      capture_output=True, text=True, cwd=_REPO_ROOT, timeout=240)
                db["ok"] = proc.returncode == 0
                tail = [ln for ln in proc.stdout.splitlines() if "Total rows loaded" in ln]
                db["detail"] = tail[-1].strip() if tail else (proc.stderr or proc.stdout)[-300:]
            except Exception as e:
                db["detail"] = f"seed loader failed: {e}"
        self.reset_memory()
        # the seed loader queues a system.reset marker for other instances; this instance has just reset itself
        for ev in persistence.claim_pending_events():
            persistence.complete_events([ev["event_id"]], "reset performed by the API")
        return {"status": "reset", "database": db, "students_in_seed": len(onboarding_service.get_all_synthetic_students()),
                "plans_in_memory": len(plan_service.plans)}

    # ------------------------------------------------------------------ queue worker (Adminer / direct SQL edits)
    def process_queue_once(self) -> int:
        events = persistence.claim_pending_events()
        if not events:
            return 0
        students: Dict[str, List[int]] = {}
        done = 0
        for ev in events:
            et, eid = ev["entity_type"], ev["entity_id"]
            try:
                if et == "system.reset":
                    self.reset_memory(source="db")
                    persistence.complete_events([ev["event_id"]], "in-memory state restored to seed")
                elif et.startswith("student."):
                    students.setdefault(eid, []).append(ev["event_id"])
                    continue
                elif et == "kb.course":
                    row = persistence.fetch_course(eid)
                    if row:
                        r = self.apply_course_update(eid, {"credits": row["credits"], "title": row["title"]}, source="db")
                        persistence.complete_events([ev["event_id"]], f"course applied; {r['students_reprocessed']} student plan(s) rebuilt")
                    else:
                        persistence.complete_events([ev["event_id"]], "course row no longer exists; ignored")
                elif et == "kb.academic_rule":
                    n = 0
                    for rule in (persistence.fetch_academic_rules() or []):
                        cur = plan_service.validator.academic_rules.get(rule["rule_id"], {}).get("parameters")
                        if cur is not None and cur != rule["parameters"]:
                            n += self.apply_rule_update(rule["rule_id"], rule["parameters"], source="db")["students_reprocessed"]
                    persistence.complete_events([ev["event_id"]], f"rules applied; {n} student plan(s) rebuilt")
                else:
                    persistence.complete_events([ev["event_id"]], "no re-processing needed for this table")
                done += 1
            except Exception as e:
                logger.exception("re-processing failed for %s", ev)
                persistence.complete_events([ev["event_id"]], f"failed: {e}", status="failed")
        for sid, ids in students.items():
            try:
                if sid in onboarding_service.students or sid in plan_service.plans:
                    r = self.reprocess_student(sid, "Record edited directly in the database (Adminer / SQL).", trigger="db_edit",
                                               reload_from_db=True, source="db")
                    persistence.complete_events(ids, f"plan v{r['old_version']} -> v{r['new_version']}: {r['summary']}")
                else:
                    persistence.complete_events(ids, "student not loaded in memory; fresh state is read from the database on next access")
                done += len(ids)
            except Exception as e:
                logger.exception("re-processing failed for student %s", sid)
                persistence.complete_events(ids, f"failed: {e}", status="failed")
        return done

    def _loop(self):
        while not self._stop.is_set():
            try:
                if persistence.db_available():
                    self.process_queue_once()
            except Exception:
                logger.debug("queue poll failed", exc_info=True)
            self._stop.wait(self.poll_seconds)

    def start_worker(self):
        if self._thread and self._thread.is_alive():
            return
        if not persistence.sync_enabled():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="reprocess-worker", daemon=True)
        self._thread.start()

    def stop_worker(self):
        self._stop.set()

    def status(self) -> Dict[str, Any]:
        return {"worker_running": bool(self._thread and self._thread.is_alive()), "poll_seconds": self.poll_seconds,
                "db_sync_enabled": persistence.sync_enabled(), "db_available": persistence.db_available(),
                "recent": list(self.log)[:20], "db_queue": persistence.recent_queue(12)}

reprocess_service = ReprocessService()
