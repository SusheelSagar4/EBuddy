import os
import csv
from typing import List, Dict, Optional, Any
from app.contracts.kb import Course, Skill, Resource, AcademicRule, ResearchProject
from app.contracts.goal import Goal, GoalRequirement, MasteryCriteria

class CourseRepo:
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self._courses: Dict[str, Course] = {}
        self._load()

    def _load(self):
        course_file = os.path.join(self.seed_dir, "course.csv")
        if not os.path.exists(course_file):
            return
        with open(course_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                cid = r["course_id"]
                self._courses[cid] = Course(
                    course_id=cid,
                    course_code=r["course_code"],
                    display_code=r["display_code"],
                    code_conflict=r["code_conflict"].lower() == "true",
                    title=r["title"],
                    department_id=r.get("department_id"),
                    credits=float(r["credits"]),
                    ltp=r.get("ltp"),
                    mode=r.get("mode", "offline"),
                    level=r.get("level", "UG"),
                    status=r.get("status", "verified"),
                    source_id=r["source_id"],
                    verified=r.get("status", "verified") == "verified"
                )

    def get_by_id(self, course_id: str) -> Optional[Course]:
        return self._courses.get(course_id)

    def get_by_code(self, course_code: str) -> List[Course]:
        return [c for c in self._courses.values() if c.course_code == course_code]

    def list_all(self) -> List[Course]:
        return list(self._courses.values())

class SkillRepo:
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self._skills: Dict[str, Skill] = {}
        self._load()

    def _load(self):
        path = os.path.join(self.seed_dir, "skill.csv")
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                sid = r["skill_id"]
                self._skills[sid] = Skill(
                    skill_id=sid,
                    name=r["name"],
                    domain=r["domain"],
                    description=r["description"],
                    level_scale=r.get("level_scale", "0-100"),
                    status=r.get("status", "draft_for_review"),
                    source_id=r["source_id"],
                    verified=r.get("status") == "verified"
                )

    def get_by_id(self, skill_id: str) -> Optional[Skill]:
        return self._skills.get(skill_id)

    def list_all(self) -> List[Skill]:
        return list(self._skills.values())

class GoalRepo:
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self._goals: Dict[str, Goal] = {}
        self._load()

    def _load(self):
        path = os.path.join(self.seed_dir, "goal.csv")
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                gid = r["goal_id"]
                self._goals[gid] = Goal(
                    goal_id=gid,
                    name=r["name"],
                    category=r["category"],
                    description=r["description"],
                    status=r.get("status", "draft_for_review"),
                    source_id=r["source_id"],
                    verified=r.get("status") == "verified"
                )

    def get_by_id(self, goal_id: str) -> Optional[Goal]:
        return self._goals.get(goal_id)

    def list_all(self) -> List[Goal]:
        return list(self._goals.values())

class ResourceRepo:
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self._resources: Dict[str, Resource] = {}
        self._load()

    def _load(self):
        path = os.path.join(self.seed_dir, "resource.csv")
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rid = r["resource_id"]
                self._resources[rid] = Resource(
                    resource_id=rid,
                    title=r["title"],
                    url=r["url"],
                    provider=r["provider"],
                    media_type=r.get("media_type") or r.get("resource_type", "playlist"),
                    coverage_status=r["coverage_status"],
                    link_verified=r.get("link_verified", "").lower() == "true",
                    status=r.get("status", "verified"),
                    source_id=r["source_id"],
                    verified=r.get("status", "verified") == "verified"
                )

    def get_by_id(self, resource_id: str) -> Optional[Resource]:
        return self._resources.get(resource_id)

    def list_all(self) -> List[Resource]:
        return list(self._resources.values())

class RuleRepo:
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self._rules: Dict[str, AcademicRule] = {}
        self._load()

    def _load(self):
        import json
        path = os.path.join(self.seed_dir, "academic_rule.json")
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            rules_data = json.load(f)
            for r in rules_data:
                rid = r["rule_id"]
                self._rules[rid] = AcademicRule(
                    rule_id=rid,
                    rule_type=r["rule_type"],
                    parameters=r["parameters"],
                    human_text=r["human_text"],
                    status=r.get("status", "unsourced_baseline"),
                    source_id=r["source_id"],
                    verified=r.get("status") == "verified"
                )

    def get_by_id(self, rule_id: str) -> Optional[AcademicRule]:
        return self._rules.get(rule_id)

    def list_all(self) -> List[AcademicRule]:
        return list(self._rules.values())

