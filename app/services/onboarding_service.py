from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from app.contracts.student import StudentProfile, Constraint, Preference
from app.contracts.goal import Goal
from app.kb.repositories import GoalRepo

class OnboardingService:
    def __init__(self):
        self.goal_repo = GoalRepo()
        # Active in-memory session store (or backed by DB)
        self.students: Dict[str, StudentProfile] = {}
        self.completed_courses: Dict[str, List[str]] = {}
        self.goals: Dict[str, Goal] = {}
        self.constraints: Dict[str, List[Constraint]] = {}
        self.preferences: Dict[str, List[Preference]] = {}

    def onboard_student(
        self,
        student_id: str,
        name: str,
        programme_id: str,
        current_semester: int,
        cgpa: Optional[float] = None,
        backlogs: int = 0,
        goal_id: str = "GOAL_EE_CORE_POWER",
        completed_course_ids: Optional[List[str]] = None,
        constraints: Optional[List[Dict[str, Any]]] = None,
        preferences: Optional[List[Dict[str, Any]]] = None
    ) -> StudentProfile:
        student = StudentProfile(
            student_id=student_id,
            name=name,
            programme_id=programme_id,
            current_semester=current_semester,
            cgpa=cgpa,
            backlogs=backlogs,
            is_synthetic=True,
            created_at=datetime.now(timezone.utc)
        )
        self.students[student_id] = student
        self.completed_courses[student_id] = completed_course_ids or []
        
        goal = self.goal_repo.get_by_id(goal_id)
        if not goal:
            goal = Goal(
                goal_id=goal_id,
                name="Power Systems & Smart Grid",
                category="career",
                description="Core electrical and power engineering",
                source_id="DESIGN_TEAM"
            )
        self.goals[student_id] = goal

        self.constraints[student_id] = [
            Constraint(constraint_id=f"C_{student_id}_{i}", student_id=student_id, constraint_type=c.get("type", "study_hours"), parameters=c)
            for i, c in enumerate(constraints or [])
        ]
        self.preferences[student_id] = [
            Preference(preference_id=f"P_{student_id}_{i}", student_id=student_id, preference_type=p.get("type", "mode"), value=p.get("value", "offline"))
            for i, p in enumerate(preferences or [])
        ]

        return student

onboarding_service = OnboardingService()

