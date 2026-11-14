import os
import csv
import json
from typing import Dict, List, Any, Optional
from app.contracts.student import StudentProfile
from app.contracts.plan import Plan, ValidationReport, ValidationCheck
from app.engine.interfaces import IPlanValidator

class PlanValidator(IPlanValidator):
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self.valid_courses: Dict[str, Dict[str, Any]] = {}
        self.prereqs: Dict[str, List[str]] = {}
        self.academic_rules: Dict[str, Dict[str, Any]] = {}
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        # 1. Courses
        course_file = os.path.join(self.seed_dir, "course.csv")
        if os.path.exists(course_file):
            with open(course_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    self.valid_courses[r["course_id"]] = {
                        "credits": float(r.get("credits", 0.0)),
                        "title": r.get("title", ""),
                        "display_code": r.get("display_code", "")
                    }

        # 2. Prerequisites
        prereq_file = os.path.join(self.seed_dir, "course_prerequisite.csv")
        if os.path.exists(prereq_file):
            with open(prereq_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    cid = r["course_id"].strip()
                    pid = r["prereq_id"].strip()
                    self.prereqs.setdefault(cid, []).append(pid)

        # 3. Academic Rules
        rule_file = os.path.join(self.seed_dir, "academic_rule.json")
        if os.path.exists(rule_file):
            with open(rule_file, "r", encoding="utf-8") as f:
                rules = json.load(f)
                for r in rules:
                    self.academic_rules[r["rule_id"]] = r

    def validate_plan(self, plan: Plan, student: StudentProfile, completed_course_ids: Optional[List[str]] = None) -> ValidationReport:
        checks: List[ValidationCheck] = []
        messages: List[str] = []
        completed_set = set(completed_course_ids or [])

        # 1. Course Existence Check
        missing_courses = []
        course_items = [it for it in plan.items if it.item_type == "course" and it.course_id]
        for it in course_items:
            cid = it.course_id
            if cid not in self.valid_courses:
                missing_courses.append(cid)

        if missing_courses:
            msg = f"Unknown course_id(s) cited in plan: {', '.join(missing_courses)}"
            checks.append(ValidationCheck(check_name="course_existence", passed=False, severity="error", message=msg))
            messages.append(msg)
        else:
            checks.append(ValidationCheck(check_name="course_existence", passed=True, severity="info", message="All course codes exist in institutional catalog."))

        # 2. Prerequisite Satisfaction Check
        prereq_violations = []
        scheduled_so_far = set(completed_set)
        for it in course_items:
            cid = it.course_id
            required = self.prereqs.get(cid, [])
            for p in required:
                if p not in scheduled_so_far:
                    prereq_violations.append(f"Course {cid} requires {p} which has not been completed or scheduled prior.")
            scheduled_so_far.add(cid)

        if prereq_violations:
            msg = "; ".join(prereq_violations)
            checks.append(ValidationCheck(check_name="prerequisites", passed=False, severity="error", message=msg))
            messages.append(msg)
        else:
            checks.append(ValidationCheck(check_name="prerequisites", passed=True, severity="info", message="All course prerequisites satisfied."))

        # 3. No Already Mastered / Completed Content
        mastered_violations = []
        for it in course_items:
            if it.course_id in completed_set:
                mastered_violations.append(f"Course {it.course_id} is already completed by student.")

        if mastered_violations:
            msg = "; ".join(mastered_violations)
            checks.append(ValidationCheck(check_name="no_duplicate_mastery", passed=False, severity="error", message=msg))
            messages.append(msg)
        else:
            checks.append(ValidationCheck(check_name="no_duplicate_mastery", passed=True, severity="info", message="No previously completed courses re-assigned."))

        # 4. Academic Credit Cap Rules
        # Calculate semester total credits
        sem_credits = 0.0
        for it in course_items:
            sem_credits += self.valid_courses.get(it.course_id, {}).get("credits", 0.0)

        for rule_id, rule in self.academic_rules.items():
            if rule.get("rule_type") == "credit_cap":
                params = rule.get("parameters", {})
                max_cr = float(params.get("max_credits", 26.0))
                min_cr = float(params.get("min_credits", 16.0))
                is_baseline = (rule.get("status") == "unsourced_baseline")

                # If student on probation / low CGPA
                if (student.cgpa or 7.0) < 6.00 and "PROBATION" in rule_id:
                    cap = float(params.get("max_credits", 18.0))
                    if sem_credits > cap:
                        msg = f"Credit total {sem_credits} exceeds probation cap of {cap}."
                        sev = "warning" if is_baseline else "error"
                        checks.append(ValidationCheck(check_name=rule_id, passed=is_baseline, severity=sev, message=msg))
                        messages.append(f"[{sev.upper()}] {msg}")
                elif "REGULAR" in rule_id:
                    if sem_credits > max_cr:
                        msg = f"Credit total {sem_credits} exceeds maximum regular cap of {max_cr}."
                        sev = "warning" if is_baseline else "error"
                        checks.append(ValidationCheck(check_name=rule_id, passed=is_baseline, severity=sev, message=msg))
                        messages.append(f"[{sev.upper()}] {msg}")
                    else:
                        checks.append(ValidationCheck(check_name=rule_id, passed=True, severity="info", message="Credit load within permissible limits."))

        # Overall pass if no error-severity check failed
        passed = all(c.passed for c in checks if c.severity == "error")

        return ValidationReport(
            plan_id=plan.plan_id,
            passed=passed,
            checks=checks,
            messages=messages
        )
