import os
import csv
from typing import Dict, Any, List, Optional
from app.contracts.student import StudentProfile
from app.contracts.goal import Goal, GoalRequirement
from app.contracts.plan import Plan, ValidationReport
from app.engine.planner import Planner
from app.engine.validator import PlanValidator
from app.engine.gaps import GapAnalyzer
from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service

class PlanService:
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self.planner = Planner(seed_dir)
        self.validator = PlanValidator(seed_dir)
        self.gap_analyzer = GapAnalyzer()
        self.plans: Dict[str, Plan] = {}
        self.goal_requirements: Dict[str, List[GoalRequirement]] = {}
        self._load_requirements()

    def _load_requirements(self):
        path = os.path.join(self.seed_dir, "goal_skill_requirement.csv")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    gid = r["goal_id"]
                    self.goal_requirements.setdefault(gid, []).append(GoalRequirement(
                        goal_id=gid,
                        skill_id=r["skill_id"],
                        required_level=float(r["required_level"]),
                        importance=float(r.get("importance", 1.0)),
                        source_id=r.get("source_id", "DESIGN_TEAM")
                    ))

    def create_or_update_plan(self, student_id: str) -> Dict[str, Any]:
        student = onboarding_service.students.get(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not onboarded")

        goal = onboarding_service.goals.get(student_id)
        completed = onboarding_service.completed_courses.get(student_id, [])
        constraints = onboarding_service.constraints.get(student_id, [])
        preferences = onboarding_service.preferences.get(student_id, [])
        states = diagnostic_service.skill_states.get(student_id, [])

        reqs = self.goal_requirements.get(goal.goal_id, [])
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, states)

        # Generate candidate plan
        plan = self.planner.generate_plan(
            student=student,
            goal=goal,
            gaps=gaps,
            constraints=constraints,
            preferences=preferences,
            completed_course_ids=completed
        )

        # Validate with deterministic validator
        report = self.validator.validate_plan(plan, student, completed_course_ids=completed)
        plan_with_report = plan.model_copy(update={"validation_report": report})
        self.plans[student_id] = plan_with_report

        return {
            "plan": plan_with_report.model_dump(),
            "gaps": gaps,
            "validation": report.model_dump()
        }

    def get_plan(self, student_id: str) -> Optional[Plan]:
        return self.plans.get(student_id)

plan_service = PlanService()

