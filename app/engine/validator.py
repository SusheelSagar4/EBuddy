"""
Deterministic Plan Validator.

Runs ALL checks on ANY plan - whether produced by the planner, by an approved
ChangeProposal, or suggested by the LLM. Nothing reaches the student unless it passes.

Checks (per semester where relevant)
  course_existence      every course_id exists in kb.course (zero hallucinated codes)
  resource_existence    every resource_id exists in the KB / track KB / persona resource files
  prerequisites         prerequisites completed or scheduled in an earlier-or-same semester, before the dependent
  no_duplicate_mastery  no completed course re-assigned; no course scheduled twice
  RULE_SEM_CREDIT_CAP_* institute credit caps (unsourced baseline -> labelled warning, never a hard fail)
  student_credit_cap    student-stated credit cap (HARD)
  student_weekly_hours  student-stated weekly-hours cap for the current semester (HARD)
"""
import logging
import os
import csv
import glob
import json
from typing import Dict, List, Any, Optional, Set
from app.contracts.student import StudentProfile, Constraint
from app.contracts.plan import Plan, ValidationReport, ValidationCheck
from app.engine.interfaces import IPlanValidator


class PlanValidator(IPlanValidator):
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self.valid_courses: Dict[str, Dict[str, Any]] = {}
        self.prereqs: Dict[str, List[str]] = {}
        self.academic_rules: Dict[str, Dict[str, Any]] = {}
        self.valid_resources: Set[str] = set()
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        self.valid_courses.clear(); self.prereqs.clear(); self.academic_rules.clear(); self.valid_resources.clear()
        course_file = os.path.join(self.seed_dir, "course.csv")
        if os.path.exists(course_file):
            with open(course_file, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.valid_courses[r["course_id"]] = {
                        "credits": float(r.get("credits") or 0.0),
                        "title": r.get("title", ""),
                        "display_code": r.get("display_code", "")
                    }

        prereq_file = os.path.join(self.seed_dir, "course_prerequisite.csv")
        if os.path.exists(prereq_file):
            with open(prereq_file, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.prereqs.setdefault(r["course_id"].strip(), []).append(r["prereq_id"].strip())

        rule_file = os.path.join(self.seed_dir, "academic_rule.json")
        if os.path.exists(rule_file):
            with open(rule_file, "r", encoding="utf-8") as f:
                for r in json.load(f):
                    self.academic_rules[r["rule_id"]] = r

        self.prog_cores: Dict[Any, Set[str]] = {}
        pr_file = os.path.join(self.seed_dir, "programme_requirement.csv")
        if os.path.exists(pr_file):
            with open(pr_file, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    p = r["programme_id"].strip().upper()
                    try:
                        sem = int(float(r["semester_number"]))
                    except (ValueError, TypeError):
                        continue
                    cid = (r.get("course_id") or "").strip()
                    if cid:
                        self.prog_cores.setdefault((p, sem), set()).add(cid)

        # Known resource identifiers (KB + career tracks + persona resource files)
        res_file = os.path.join(self.seed_dir, "resource.csv")
        if os.path.exists(res_file):
            with open(res_file, "r", encoding="utf-8") as f:
                self.valid_resources.update(r["resource_id"] for r in csv.DictReader(f))
        try:
            from app.kb.track_repo import TrackRepo
            self.valid_resources.update(TrackRepo().all_resource_ids())
        except Exception:
            # without these ids every plan with career-track resources fails the resource check
            logging.getLogger("ebuddy.validator").exception("Career-track resource ids could not be loaded")
        root = os.path.abspath(os.path.join(self.seed_dir, "..", "..", ".."))
        for pattern in (os.path.join(root, "data", "raw", "higher_studies", "*", "resources.csv"),
                        os.path.join(root, "data", "seed", "mba", "mba_resources.csv")):
            for path in glob.glob(pattern):
                try:
                    with open(path, "r", encoding="utf-8-sig") as f:
                        for r in csv.DictReader(f):
                            rid = (r.get("resource_id") or r.get("id") or "").strip()
                            if rid:
                                self.valid_resources.add(rid)
                except Exception:
                    logging.getLogger("ebuddy.validator").warning("Skipping unreadable resource file %s", path, exc_info=True)
                    continue

    @staticmethod
    def _constraint_values(constraints: Optional[List[Constraint]]) -> Dict[str, Optional[float]]:
        cap, headroom, hours = None, 0.0, None
        for c in (constraints or []):
            if not getattr(c, "is_active", True):
                continue
            t = (c.constraint_type or "").lower()
            p = c.parameters or {}
            if t in ("credit_cap", "max_credits", "max_credits_per_sem"):
                v = p.get("max_credits") or p.get("credit_cap") or p.get("credits") or p.get("value")
                cap = float(v) if v is not None else cap
            elif t == "headroom":
                v = p.get("headroom") or p.get("credit_headroom") or p.get("value")
                headroom = float(v) if v is not None else headroom
            elif t in ("weekly_hours", "max_weekly_hours", "study_hours", "weekly_study_hours", "max_hours_per_week"):
                v = p.get("max_hours") or p.get("weekly_hours") or p.get("hours") or p.get("value")
                hours = float(v) if v is not None else hours
        if cap is not None:
            cap = cap - headroom
        elif headroom > 0:
            cap = 26.0 - headroom
        return {"credit_cap": cap, "weekly_hours": hours}

    def validate_plan(
        self,
        plan: Plan,
        student: StudentProfile,
        completed_course_ids: Optional[List[str]] = None,
        constraints: Optional[List[Constraint]] = None,
    ) -> ValidationReport:
        checks: List[ValidationCheck] = []
        messages: List[str] = []
        completed_set = set(completed_course_ids or [])
        current_sem = student.current_semester or 1

        # A student with zero backlogs has cleared all prior-semester courses even if the transcript list is sparse
        if (completed_course_ids is None or (student.backlogs or 0) == 0) and current_sem > 1:
            raw_p = (student.programme_id or "").upper().strip()
            prog = "BTECH_MM" if raw_p in ["BTECH_MME", "MME", "MM"] else ("BTECH_EE" if raw_p in ["BTECH_EE", "EE"] else raw_p)
            for s in range(1, current_sem):
                completed_set.update(self.prog_cores.get((prog, s), set()))
            if prog == "BTECH_EE" and current_sem >= 3:
                completed_set.update(["MA1L001", "MA1L002", "EE1L001", "CS1L001"])
                if current_sem >= 3:
                    # the whole first-year common core (both A/B halves) is behind a Year-2+ student with no backlog
                    completed_set.update(["PH1L001", "PH1P001", "ME1L001", "ME1P001", "EE1P001",
                                          "CY1L001", "CY1P001", "CS1P001", "CE1P001", "ID1T001", "ID1T002"])

        indexed = list(enumerate(plan.items))
        course_items = [(i, it) for i, it in indexed if it.item_type == "course" and it.course_id]
        course_items.sort(key=lambda p: ((p[1].semester_number or current_sem), p[0]))

        # 1. Course existence (zero hallucinated course codes)
        missing = sorted({it.course_id for _i, it in course_items if it.course_id not in self.valid_courses})
        if missing:
            msg = f"Unknown course_id(s) cited in plan: {', '.join(missing)}"
            checks.append(ValidationCheck(check_name="course_existence", passed=False, severity="error", message=msg))
            messages.append(msg)
        else:
            checks.append(ValidationCheck(check_name="course_existence", passed=True, severity="info", message="All course codes exist in institutional catalog."))

        # 1b. Resource existence (zero hallucinated resource ids)
        unknown_res = sorted({it.resource_id for it in plan.items if it.resource_id and it.resource_id not in self.valid_resources})
        if unknown_res:
            msg = f"Unknown resource_id(s) cited in plan: {', '.join(unknown_res)}"
            checks.append(ValidationCheck(check_name="resource_existence", passed=False, severity="error", message=msg))
            messages.append(msg)
        else:
            checks.append(ValidationCheck(check_name="resource_existence", passed=True, severity="info", message="All resource ids exist in the knowledge base."))

        # 2. Prerequisites (earlier-or-same semester, listed before the dependent)
        prereq_violations = []
        scheduled_so_far = set(completed_set)
        for _i, it in course_items:
            for p in self.prereqs.get(it.course_id, []):
                if p not in scheduled_so_far:
                    prereq_violations.append(f"Course {it.course_id} requires {p} which has not been completed or scheduled prior.")
            scheduled_so_far.add(it.course_id)
        if prereq_violations:
            msg = "; ".join(prereq_violations)
            checks.append(ValidationCheck(check_name="prerequisites", passed=False, severity="error", message=msg))
            messages.append(msg)
        else:
            checks.append(ValidationCheck(check_name="prerequisites", passed=True, severity="info", message="All course prerequisites satisfied."))

        # 3. No completed course re-assigned, no course scheduled twice
        mastered_violations = [f"Course {it.course_id} is already completed by student." for _i, it in course_items if it.course_id in completed_set]
        seen: Set[str] = set()
        for _i, it in course_items:
            if it.course_id in seen:
                mastered_violations.append(f"Course {it.course_id} is scheduled more than once.")
            seen.add(it.course_id)
        if mastered_violations:
            msg = "; ".join(mastered_violations)
            checks.append(ValidationCheck(check_name="no_duplicate_mastery", passed=False, severity="error", message=msg))
            messages.append(msg)
        else:
            checks.append(ValidationCheck(check_name="no_duplicate_mastery", passed=True, severity="info", message="No previously completed courses re-assigned."))

        # 4. Credit caps, evaluated PER SEMESTER
        sem_credits: Dict[int, float] = {}
        for _i, it in course_items:
            sem = it.semester_number or current_sem
            sem_credits[sem] = sem_credits.get(sem, 0.0) + self.valid_courses.get(it.course_id, {}).get("credits", 0.0)
        for it in plan.items:
            # open degree slots (no course chosen yet) still reserve their credits
            if it.item_type == "course" and not it.course_id and it.credits:
                sem = it.semester_number or current_sem
                sem_credits[sem] = sem_credits.get(sem, 0.0) + float(it.credits)

        for rule_id, rule in self.academic_rules.items():
            if rule.get("rule_type") != "credit_cap":
                continue
            params = rule.get("parameters", {})
            max_cr = float(params.get("max_credits", 26.0))
            is_baseline = (rule.get("status") == "unsourced_baseline")
            sev = "warning" if is_baseline else "error"
            if "PROBATION" in rule_id:
                if (student.cgpa or 7.0) >= float(params.get("cgpa_threshold", 6.0)):
                    continue
                over = {s: c for s, c in sorted(sem_credits.items()) if c > max_cr}
                if over:
                    msg = "; ".join(f"Semester {s}: credit total {c} exceeds probation cap of {max_cr}." for s, c in over.items())
                    checks.append(ValidationCheck(check_name=rule_id, passed=is_baseline, severity=sev, message=msg))
                    messages.append(f"[{sev.upper()}] {msg}")
                else:
                    checks.append(ValidationCheck(check_name=rule_id, passed=True, severity="info", message="Credit load within probation limit in every planned semester."))
            elif "REGULAR" in rule_id:
                over = {s: c for s, c in sorted(sem_credits.items()) if c > max_cr}
                if over:
                    msg = "; ".join(f"Semester {s}: Credit total {c} exceeds maximum regular cap of {max_cr}." for s, c in over.items())
                    checks.append(ValidationCheck(check_name=rule_id, passed=is_baseline, severity=sev, message=msg))
                    messages.append(f"[{sev.upper()}] {msg}")
                else:
                    checks.append(ValidationCheck(check_name=rule_id, passed=True, severity="info", message="Credit load within permissible limits."))

        # 5. Student-stated constraints are HARD
        cv = self._constraint_values(constraints)
        if cv["credit_cap"] is not None:
            cap = cv["credit_cap"]
            over = {s: c for s, c in sorted(sem_credits.items()) if c > cap + 1e-9}
            if over:
                msg = "; ".join(f"Semester {s}: credit total {c} exceeds the student's stated limit of {cap}." for s, c in over.items())
                checks.append(ValidationCheck(check_name="student_credit_cap", passed=False, severity="error", message=msg))
                messages.append(msg)
            else:
                checks.append(ValidationCheck(check_name="student_credit_cap", passed=True, severity="info",
                                              message=f"Every planned semester is within the student's stated limit of {cap} credits."))
        if cv["weekly_hours"] is not None:
            cap_h = cv["weekly_hours"]
            used = round(sum((it.prep_hours_weekly or 0.0) for it in plan.items
                             if (it.semester_number or current_sem) == current_sem and it.planning_status in (None, "current")), 1)
            if used > cap_h + 0.05:
                msg = f"Current-semester weekly self-study of {used} h exceeds the student's stated cap of {cap_h} h."
                checks.append(ValidationCheck(check_name="student_weekly_hours", passed=False, severity="error", message=msg))
                messages.append(msg)
            else:
                checks.append(ValidationCheck(check_name="student_weekly_hours", passed=True, severity="info",
                                              message=f"Weekly self-study ({used} h) is within the student's stated cap of {cap_h} h."))

        passed = all(c.passed for c in checks if c.severity == "error")
        return ValidationReport(plan_id=plan.plan_id, passed=passed, checks=checks, messages=messages)
