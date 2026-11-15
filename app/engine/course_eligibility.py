import os
import csv
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel

from app.contracts.student import StudentProfile
from app.kb.repositories import CourseRepo
from app.kb.field_repo import field_repo

class EligibilityResult(BaseModel):
    is_eligible: bool
    reason: str
    rule_name: str
    missing_prerequisites: List[str] = []
    cgpa_required: Optional[float] = None
    cgpa_actual: Optional[float] = None
    semester_required: Optional[int] = None

class CourseEligibilityEngine:
    """
    Unified Deterministic Course Eligibility Engine (Requirement F8).
    
    Evaluates:
    1. Prerequisite completion (strict DAG gating).
    2. Minimum CGPA threshold (e.g. Minors >= 8.0, Honors >= 8.5, regular >= 0.0).
    3. Maximum active backlogs (Minors and overloads require 0 backlogs).
    4. Branch / Programme restrictions (e.g. EE core restricted to EE, MME core to MME, minors open).
    5. Semester offering and parity (Odd vs Even semester; Minors allowed only in Sem >= 5).
    """
    def __init__(self, seed_dir: Optional[str] = None):
        self.course_repo = CourseRepo(seed_dir)
        self.field_repo = field_repo
        self.prereqs: Dict[str, List[str]] = {}
        self.offerings: Dict[str, List[Dict[str, Any]]] = {}
        self._load_prereqs_and_offerings(seed_dir)

    def _load_prereqs_and_offerings(self, seed_dir: Optional[str] = None):
        sdir = seed_dir or os.path.join(os.path.dirname(__file__), "..", "..", "data", "seed", "kb")
        # Prereqs
        pfile = os.path.join(sdir, "course_prerequisite.csv")
        if os.path.exists(pfile):
            with open(pfile, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    cid = r["course_id"].strip()
                    pid = r["prereq_id"].strip()
                    self.prereqs.setdefault(cid, []).append(pid)

        # Offerings
        ofile = os.path.join(sdir, "course_offering.csv")
        if os.path.exists(ofile):
            with open(ofile, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    cid = r["course_id"].strip()
                    self.offerings.setdefault(cid, []).append(r)

    def check_eligibility(
        self,
        student: StudentProfile,
        course_id: str,
        target_semester: Optional[int] = None,
        completed_course_ids: Optional[List[str]] = None
    ) -> EligibilityResult:
        completed = set(completed_course_ids or [])
        t_sem = target_semester or student.current_semester

        # 1. Check Course Existence in KB
        course_obj = self.course_repo.get_by_id(course_id)
        if not course_obj:
            return EligibilityResult(
                is_eligible=False,
                reason=f"Course '{course_id}' does not exist in knowledge base.",
                rule_name="RULE_COURSE_EXISTS"
            )

        # 2. Check Prerequisite DAG
        required_prereqs = self.prereqs.get(course_id, [])
        missing = [p for p in required_prereqs if p not in completed]
        if missing:
            return EligibilityResult(
                is_eligible=False,
                reason=f"Unmet prerequisites: Student has not completed {', '.join(missing)}.",
                rule_name="RULE_PREREQUISITE_GATE",
                missing_prerequisites=missing
            )

        # 3. Check CGPA & Backlogs via course_eligibility rules
        elig_rule = self.field_repo.get_course_eligibility(course_id)
        min_cgpa = 0.0
        min_sem = 1
        max_backlogs = 99
        allowed_progs = ["ANY"]
        rule_name = "RULE_REGULAR_COURSE_ELIGIBILITY"

        if elig_rule:
            min_cgpa = elig_rule.get("min_cgpa", 0.0)
            min_sem = elig_rule.get("min_semester", 1)
            max_backlogs = elig_rule.get("max_backlogs", 99)
            allowed_progs = elig_rule.get("allowed_programmes", ["ANY"])
            rule_name = elig_rule.get("rule_name", rule_name)

        student_cgpa = float(student.cgpa) if student.cgpa is not None else 8.0
        if student_cgpa < min_cgpa:
            return EligibilityResult(
                is_eligible=False,
                reason=f"CGPA {student_cgpa:.2f} is below minimum requirement of {min_cgpa:.2f} for {course_id}.",
                rule_name=rule_name,
                cgpa_required=min_cgpa,
                cgpa_actual=student_cgpa
            )

        if student.backlogs > max_backlogs:
            return EligibilityResult(
                is_eligible=False,
                reason=f"Active backlogs ({student.backlogs}) exceed maximum allowed ({max_backlogs}) for {course_id}.",
                rule_name=rule_name
            )

        # 4. Check Minimum Semester
        if t_sem < min_sem:
            return EligibilityResult(
                is_eligible=False,
                reason=f"Course {course_id} is only permitted from Semester {min_sem} onwards (student is in Semester {t_sem}).",
                rule_name=rule_name,
                semester_required=min_sem
            )

        # 5. Check Branch / Programme Restriction
        prog = student.programme_id.strip().upper()
        if "ANY" not in allowed_progs and prog not in allowed_progs:
            return EligibilityResult(
                is_eligible=False,
                reason=f"Course {course_id} is restricted to programmes {', '.join(allowed_progs)}; student belongs to {prog}.",
                rule_name="RULE_PROGRAMME_BRANCH_RESTRICTION"
            )

        # 6. Check Semester Offering & Parity
        course_offers = self.offerings.get(course_id, [])
        if course_offers:
            offered_sems = [int(o["semester_number"]) for o in course_offers if o.get("semester_number")]
            offered_parities = [o.get("parity", "").lower() for o in course_offers if o.get("parity")]
            target_parity = "odd" if (t_sem % 2 == 1) else "even"

            if offered_parities and target_parity not in offered_parities and t_sem not in offered_sems:
                return EligibilityResult(
                    is_eligible=False,
                    reason=f"Course {course_id} is only offered in {', '.join(set(offered_parities))} semesters (requested Semester {t_sem} is {target_parity}).",
                    rule_name="RULE_SEMESTER_OFFERING_PARITY"
                )

        return EligibilityResult(
            is_eligible=True,
            reason=f"Student satisfies all academic rules, prerequisites, and CGPA requirements for {course_id}.",
            rule_name=rule_name,
            cgpa_required=min_cgpa,
            cgpa_actual=student_cgpa
        )

course_eligibility_engine = CourseEligibilityEngine()

