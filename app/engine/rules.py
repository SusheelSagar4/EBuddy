import os
import csv
from typing import List, Dict, Set
from app.contracts.student import StudentProfile
from app.contracts.kb import AcademicRule
from app.engine.interfaces import IRuleEngine

class RuleEngine(IRuleEngine):
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self.prereqs: Dict[str, Set[str]] = {}
        self._load_prereqs()

    def _load_prereqs(self):
        path = os.path.join(self.seed_dir, "course_prerequisite.csv")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    cid = r["course_id"].strip()
                    pid = r["prereq_id"].strip()
                    if cid not in self.prereqs:
                        self.prereqs[cid] = set()
                    self.prereqs[cid].add(pid)

    def check_prerequisites(self, course_id: str, completed_course_ids: List[str]) -> bool:
        required = self.prereqs.get(course_id, set())
        completed_set = set(completed_course_ids)
        return required.issubset(completed_set)

    def check_credit_cap(self, student: StudentProfile, total_semester_credits: float) -> bool:
        # Default: 16-26 normal, overload up to 30 with CGPA >= 8.5
        cgpa = student.cgpa or 7.0
        if cgpa >= 8.50:
            return total_semester_credits <= 30.0
        elif cgpa < 6.00 or student.backlogs > 0:
            return total_semester_credits <= 18.0
        return total_semester_credits <= 26.0

    def _rule_params(self, rule_id: str) -> dict:
        import json
        if not hasattr(self, "_rules_cache"):
            self._rules_cache = {}
            path = os.path.join(self.seed_dir, "academic_rule.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    for r in json.load(f):
                        self._rules_cache[r["rule_id"]] = r.get("parameters", {})
        return self._rules_cache.get(rule_id, {})

    def minor_cutoff(self) -> float:
        return float(self._rule_params("RULE_MINOR_ELIGIBILITY").get("min_cgpa", 8.0))

    def check_minor_eligibility(self, student: StudentProfile) -> bool:
        # Eligible from Sem V with CGPA >= cutoff (RULE_MINOR_ELIGIBILITY, unsourced baseline) and no active backlog.
        # The comparison is exact: 7.99 is NOT eligible, 8.00 is.
        p = self._rule_params("RULE_MINOR_ELIGIBILITY")
        cgpa = student.cgpa or 0.0
        return (student.current_semester >= int(p.get("start_semester", 5))
                and cgpa >= float(p.get("min_cgpa", 8.0))
                and student.backlogs == 0)

