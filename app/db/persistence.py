"""
Best-effort PostgreSQL persistence helpers (psycopg, short timeouts, never raise to callers).

The deterministic engine works fully in memory from the seed files; when PostgreSQL is reachable the
same state is mirrored there so that it can be inspected and edited in Adminer. Connection settings
come only from the environment (DATABASE_URL / LOCAL_DATABASE_URL) - nothing is hard-coded.

EBUDDY_DB_SYNC=off disables every read/write here (used by the offline test-suite).
"""
import os
import json
import time
import logging
from typing import Any, Dict, List, Optional
from app.config import settings

logger = logging.getLogger("ebuddy.db")
_state = {"ok": None, "checked_at": 0.0}


def sync_enabled() -> bool:
    return os.getenv("EBUDDY_DB_SYNC", "auto").strip().lower() not in ("off", "0", "false", "no")


def dsn() -> str:
    return settings.effective_db_url.replace("postgresql+psycopg://", "postgresql://")


def connect(timeout: int = 2):
    import psycopg
    return psycopg.connect(dsn(), connect_timeout=timeout)


def db_available(ttl: float = 10.0) -> bool:
    if not sync_enabled():
        return False
    now = time.time()
    if _state["ok"] is not None and now - _state["checked_at"] < ttl:
        return bool(_state["ok"])
    try:
        with connect(1) as c, c.cursor() as cur:
            cur.execute("SELECT 1 FROM information_schema.tables WHERE table_schema='student' AND table_name='student'")
            _state["ok"] = cur.fetchone() is not None
    except Exception:
        _state["ok"] = False
    _state["checked_at"] = now
    return bool(_state["ok"])


def _run(fn, default=None):
    if not db_available():
        return default
    try:
        with connect() as c:
            with c.cursor() as cur:
                cur.execute("SELECT set_config('ebuddy.source', 'api', false)")
                out = fn(cur)
            c.commit()
            return out
    except Exception as e:
        logger.debug("DB operation skipped: %s", e)
        _state["checked_at"] = 0.0
        return default


# ----------------------------------------------------------------------------- reads
def fetch_student_bundle(student_id: str) -> Optional[Dict[str, Any]]:
    def q(cur):
        cur.execute("""SELECT student_id, programme_id, year, current_semester, cgpa, persona_tag, name, backlogs,
                              first_year_track, edge_case_tags, aims FROM student.student WHERE student_id=%s""", (student_id,))
        r = cur.fetchone()
        if not r:
            return None
        b: Dict[str, Any] = {"profile": dict(student_id=r[0], programme_id=r[1], year=r[2], current_semester=r[3],
                                             cgpa=float(r[4]) if r[4] is not None else None, persona_tag=r[5], name=r[6],
                                             backlogs=r[7] or 0, first_year_track=r[8] or "A",
                                             edge_case_tags=[t for t in (r[9] or "").split(";") if t], aims=r[10])}
        cur.execute("SELECT course_id, grade, semester, is_backlog FROM student.completed_course WHERE student_id=%s ORDER BY semester, id", (student_id,))
        b["courses"] = [dict(course_id=x[0], grade=x[1], semester=x[2], is_backlog=bool(x[3])) for x in cur.fetchall()]
        cur.execute("SELECT goal_id, priority, status, since_semester FROM student.goal WHERE student_id=%s ORDER BY priority, id", (student_id,))
        b["goals"] = [dict(goal_id=x[0], priority=x[1], status=x[2] or "active", since_semester=x[3]) for x in cur.fetchall()]
        cur.execute("SELECT topic, weight, declared_strength FROM student.interest WHERE student_id=%s ORDER BY id", (student_id,))
        b["interests"] = [dict(topic=x[0], weight=float(x[1] or 1.0), declared_strength=x[2], reliability_tier="weak") for x in cur.fetchall()]
        cur.execute("""SELECT evidence_id, skill_id, source_type, score, recorded_at, reliability_tier, notes
                       FROM student.skill_evidence WHERE student_id=%s ORDER BY recorded_at, evidence_id""", (student_id,))
        b["evidence"] = [dict(evidence_id=f"EV_DB_{x[0]}", skill_id=x[1], source_type=x[2], score=float(x[3]),
                              recorded_at=x[4], reliability_tier=x[5], notes=x[6]) for x in cur.fetchall()]
        cur.execute("SELECT constraint_type, parameters FROM student.constraint WHERE student_id=%s ORDER BY constraint_id", (student_id,))
        b["constraints"] = [dict(constraint_type=x[0], parameters=x[1] if isinstance(x[1], dict) else json.loads(x[1] or "{}")) for x in cur.fetchall()]
        cur.execute("SELECT preferred_learning_mode, pace FROM student.preference WHERE student_id=%s", (student_id,))
        p = cur.fetchone()
        b["preference"] = dict(preferred_learning_mode=p[0], pace=p[1]) if p else None
        return b
    return _run(q)


def fetch_course(course_id: str) -> Optional[Dict[str, Any]]:
    def q(cur):
        cur.execute("SELECT course_id, title, credits, status FROM kb.course WHERE course_id=%s", (course_id,))
        r = cur.fetchone()
        return dict(course_id=r[0], title=r[1], credits=float(r[2]), status=r[3]) if r else None
    return _run(q)


def fetch_academic_rules() -> Optional[List[Dict[str, Any]]]:
    def q(cur):
        cur.execute("SELECT rule_id, rule_type, parameters, human_text, status, source_id FROM kb.academic_rule ORDER BY rule_id")
        return [dict(rule_id=r[0], rule_type=r[1], parameters=r[2] if isinstance(r[2], dict) else json.loads(r[2] or "{}"),
                     human_text=r[3], status=r[4], source_id=r[5]) for r in cur.fetchall()]
    return _run(q)


def table_counts(tables: List[str]) -> Dict[str, int]:
    def q(cur):
        out = {}
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            out[t] = cur.fetchone()[0]
        return out
    return _run(q, {}) or {}


# ----------------------------------------------------------------------------- writes (marked as API writes)
def write_student_profile(student_id: str, fields: Dict[str, Any]) -> bool:
    allowed = {"name", "cgpa", "backlogs", "current_semester", "year", "first_year_track", "aims", "edge_case_tags"}
    sets = {k: v for k, v in fields.items() if k in allowed}
    if not sets:
        return False

    def q(cur):
        cur.execute(f"UPDATE student.student SET {', '.join(k + '=%s' for k in sets)} WHERE student_id=%s",
                    list(sets.values()) + [student_id])
        return cur.rowcount > 0
    return bool(_run(q, False))


def upsert_student(profile: Dict[str, Any]) -> bool:
    def q(cur):
        cur.execute("""INSERT INTO student.student (student_id, programme_id, year, current_semester, cgpa, is_synthetic, persona_tag,
                                                     name, backlogs, first_year_track, edge_case_tags, aims)
                       VALUES (%(student_id)s, %(programme_id)s, %(year)s, %(current_semester)s, %(cgpa)s, TRUE, %(persona_tag)s,
                               %(name)s, %(backlogs)s, %(first_year_track)s, %(edge_case_tags)s, %(aims)s)
                       ON CONFLICT (student_id) DO UPDATE SET programme_id=EXCLUDED.programme_id, year=EXCLUDED.year,
                               current_semester=EXCLUDED.current_semester, cgpa=EXCLUDED.cgpa, name=EXCLUDED.name,
                               backlogs=EXCLUDED.backlogs, aims=EXCLUDED.aims""", profile)
        return True
    return bool(_run(q, False))


def insert_evidence(student_id: str, skill_id: str, source_type: str, score: float, tier: Optional[str], notes: Optional[str]) -> bool:
    def q(cur):
        cur.execute("""INSERT INTO student.skill_evidence (student_id, skill_id, source_type, score, reliability_tier, notes)
                       VALUES (%s,%s,%s,%s,%s,%s)""", (student_id, skill_id, source_type, score, tier, notes))
        return True
    return bool(_run(q, False))


def update_evidence_score(db_evidence_id: int, score: float) -> bool:
    def q(cur):
        cur.execute("UPDATE student.skill_evidence SET score=%s WHERE evidence_id=%s", (score, db_evidence_id))
        return cur.rowcount > 0
    return bool(_run(q, False))


def set_active_goal(student_id: str, goal_id: str, since_semester: Optional[int]) -> bool:
    def q(cur):
        cur.execute("UPDATE student.goal SET status='previous', priority=2 WHERE student_id=%s AND status='active' AND goal_id<>%s", (student_id, goal_id))
        cur.execute("SELECT id FROM student.goal WHERE student_id=%s AND goal_id=%s", (student_id, goal_id))
        r = cur.fetchone()
        if r:
            cur.execute("UPDATE student.goal SET status='active', priority=1, since_semester=%s WHERE id=%s", (since_semester, r[0]))
        else:
            cur.execute("INSERT INTO student.goal (student_id, goal_id, priority, status, since_semester) VALUES (%s,%s,1,'active',%s)",
                        (student_id, goal_id, since_semester))
        return True
    return bool(_run(q, False))


def replace_constraint(student_id: str, constraint_type: str, parameters: Optional[Dict[str, Any]]) -> bool:
    def q(cur):
        cur.execute("DELETE FROM student.constraint WHERE student_id=%s AND constraint_type=%s", (student_id, constraint_type))
        if parameters is not None:
            cur.execute("INSERT INTO student.constraint (student_id, constraint_type, parameters) VALUES (%s,%s,%s)",
                        (student_id, constraint_type, json.dumps(parameters)))
        return True
    return bool(_run(q, False))


def add_avoid_course(student_id: str, course_id: str) -> bool:
    def q(cur):
        cur.execute("INSERT INTO student.constraint (student_id, constraint_type, parameters) VALUES (%s,'avoid_course',%s)",
                    (student_id, json.dumps({"course_id": course_id})))
        return True
    return bool(_run(q, False))


def write_course(course_id: str, fields: Dict[str, Any]) -> bool:
    sets = {k: v for k, v in fields.items() if k in {"title", "credits", "status"}}
    if not sets:
        return False

    def q(cur):
        cur.execute(f"UPDATE kb.course SET {', '.join(k + '=%s' for k in sets)} WHERE course_id=%s", list(sets.values()) + [course_id])
        return cur.rowcount > 0
    return bool(_run(q, False))


def write_rule_parameters(rule_id: str, parameters: Dict[str, Any]) -> bool:
    def q(cur):
        cur.execute("UPDATE kb.academic_rule SET parameters=%s WHERE rule_id=%s", (json.dumps(parameters), rule_id))
        return cur.rowcount > 0
    return bool(_run(q, False))


def persist_plan(plan_dict: Dict[str, Any], trigger: str, reason: str, diff_dict: Optional[Dict[str, Any]], previous_plan_id: Optional[str]) -> bool:
    def q(cur):
        sid = plan_dict["student_id"]
        cur.execute("SELECT 1 FROM student.student WHERE student_id=%s", (sid,))
        if not cur.fetchone():
            return False
        cur.execute("UPDATE plan.plan SET status='archived' WHERE student_id=%s AND status='active'", (sid,))
        cur.execute("""INSERT INTO plan.plan (plan_id, student_id, version, status, trigger, goal_id, reason, plan_snapshot)
                       VALUES (%s,%s,%s,'active',%s,%s,%s,%s) ON CONFLICT (plan_id) DO NOTHING""",
                    (plan_dict["plan_id"], sid, plan_dict.get("version", 1), trigger[:50], plan_dict.get("goal_id"), reason,
                     json.dumps(plan_dict, default=str)))
        for it in plan_dict.get("items", []):
            ent = it.get("course_id") or it.get("resource_id") or it.get("track_phase_id") or it.get("item_id")
            cur.execute("INSERT INTO plan.plan_item (plan_id, semester, item_type, entity_id, credits, status) VALUES (%s,%s,%s,%s,%s,%s)",
                        (plan_dict["plan_id"], it.get("semester_number") or 0, it.get("item_type"), str(ent)[:100],
                         it.get("credits") or 0.0, (it.get("planning_status") or "planned")[:20]))
        rep = plan_dict.get("validation_report") or {}
        checks = rep.get("checks", [])
        cur.execute("INSERT INTO plan.validation_report (plan_id, passed, checks_run, violations, warnings) VALUES (%s,%s,%s,%s,%s)",
                    (plan_dict["plan_id"], bool(rep.get("passed", True)), json.dumps(checks),
                     json.dumps([c for c in checks if not c.get("passed")]),
                     json.dumps([c for c in checks if c.get("severity") == "warning"])))
        if diff_dict and previous_plan_id:
            cur.execute("SELECT 1 FROM plan.plan WHERE plan_id=%s", (previous_plan_id,))
            if cur.fetchone():
                cur.execute("INSERT INTO plan.plan_diff (student_id, old_plan_id, new_plan_id, trigger, changes) VALUES (%s,%s,%s,%s,%s)",
                            (sid, previous_plan_id, plan_dict["plan_id"], trigger[:50], json.dumps(diff_dict, default=str)))
        return True
    return bool(_run(q, False))


def persist_proposal(p: Dict[str, Any]) -> bool:
    def q(cur):
        cur.execute("SELECT 1 FROM student.student WHERE student_id=%s", (p["student_id"],))
        if not cur.fetchone():
            return False
        cur.execute("""INSERT INTO plan.change_proposal (proposal_id, student_id, proposer_agent, proposal_type, status, reasoning,
                                                          target_week, target_semester, proposed_modifications, impact_summary, student_feedback)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (proposal_id) DO UPDATE SET status=EXCLUDED.status, student_feedback=EXCLUDED.student_feedback,
                                                               resolved_at=CURRENT_TIMESTAMP""",
                    (p["proposal_id"], p["student_id"], p["proposer_agent"], p["proposal_type"], p["status"], p["reasoning"],
                     p.get("target_week"), p.get("target_semester"), json.dumps(p.get("proposed_modifications", {}), default=str),
                     p["impact_summary"], p.get("student_feedback")))
        return True
    return bool(_run(q, False))


def log_llm_call(model: str, purpose: str, prompt_tokens: int, completion_tokens: int, duration_ms: int, student_id: Optional[str] = None) -> bool:
    def q(cur):
        cur.execute("""INSERT INTO ops.llm_call_log (student_id, model_name, purpose, prompt_tokens, completion_tokens, cost_usd, duration_ms)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""", (student_id, model[:100], purpose[:100], prompt_tokens, completion_tokens, 0.0, duration_ms))
        return True
    return bool(_run(q, False))


def load_memory_summary(student_id: str) -> Optional[str]:
    def q(cur):
        cur.execute("SELECT summary_text FROM ops.memory_summary WHERE student_id=%s ORDER BY updated_at DESC LIMIT 1", (student_id,))
        r = cur.fetchone()
        return r[0] if r else None
    return _run(q)


def save_memory_summary(student_id: str, text: str) -> bool:
    def q(cur):
        cur.execute("SELECT 1 FROM student.student WHERE student_id=%s", (student_id,))
        if not cur.fetchone():
            return False
        cur.execute("INSERT INTO ops.memory_summary (student_id, summary_text) VALUES (%s,%s)", (student_id, text))
        return True
    return bool(_run(q, False))


# ----------------------------------------------------------------------------- re-processing queue
def claim_pending_events(limit: int = 50) -> List[Dict[str, Any]]:
    def q(cur):
        cur.execute("""UPDATE ops.reprocess_queue SET status='processing'
                       WHERE event_id IN (SELECT event_id FROM ops.reprocess_queue WHERE status='pending' ORDER BY event_id LIMIT %s)
                       RETURNING event_id, entity_type, entity_id, action""", (limit,))
        return [dict(event_id=r[0], entity_type=r[1], entity_id=r[2], action=r[3]) for r in cur.fetchall()]
    return _run(q, []) or []


def complete_events(event_ids: List[int], result: str, status: str = "completed") -> None:
    if not event_ids:
        return

    def q(cur):
        cur.execute("UPDATE ops.reprocess_queue SET status=%s, processed_at=CURRENT_TIMESTAMP, result=%s WHERE event_id = ANY(%s)",
                    (status, result[:2000], event_ids))
    _run(q)


def recent_queue(limit: int = 15) -> List[Dict[str, Any]]:
    def q(cur):
        cur.execute("""SELECT event_id, entity_type, entity_id, action, status, enqueued_at, processed_at, result
                       FROM ops.reprocess_queue ORDER BY event_id DESC LIMIT %s""", (limit,))
        return [dict(event_id=r[0], entity_type=r[1], entity_id=str(r[2])[:120], action=r[3], status=r[4],
                     enqueued_at=str(r[5]), processed_at=str(r[6]) if r[6] else None, result=r[7]) for r in cur.fetchall()]
    return _run(q, []) or []
