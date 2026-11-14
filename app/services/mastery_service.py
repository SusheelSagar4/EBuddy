from typing import Dict, Any
from app.contracts.goal import MasteryCriteria
from app.engine.mastery import MasteryEvaluator
from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service

class MasteryService:
    def __init__(self):
        self.evaluator = MasteryEvaluator()

    def check_mastery(self, student_id: str) -> Dict[str, Any]:
        student = onboarding_service.students.get(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not found")

        goal = onboarding_service.goals.get(student_id)
        evidence = diagnostic_service.evidence_ledger.get(student_id, [])

        criteria = MasteryCriteria(
            criteria_id=f"MASTERY_{goal.goal_id}",
            goal_id=goal.goal_id,
            criteria={
                "min_skill_level": 75.0,
                "required_project_milestones": 1,
                "required_timed_assessments": 2
            },
            source_id="DESIGN_TEAM"
        )

        return self.evaluator.evaluate_mastery(student_id, goal, criteria, evidence)

mastery_service = MasteryService()

