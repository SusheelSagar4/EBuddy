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
        self.aims_and_aspirations: Dict[str, str] = {}
        self.target_timelines: Dict[str, str] = {}
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
        aims_and_aspirations: Optional[str] = None,
        target_timeline: Optional[str] = None,
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
        self.aims_and_aspirations[student_id] = aims_and_aspirations or "Excel in core engineering track"
        self.target_timelines[student_id] = target_timeline or "By Semester 7 (Placement Season)"
        
        goal = self.goal_repo.get_by_id(goal_id)
        if not goal:
            goal_names = {
                "GOAL_EE_CORE_POWER": ("Power Systems & Smart Grid", "Core electrical engineering and smart grid operations"),
                "GOAL_EE_CORE_VLSI": ("Core VLSI & Semiconductor Engineering", "Semiconductor IC design and embedded hardware"),
                "GOAL_MM_ADVANCED_MATERIALS": ("Advanced Materials R&D & Physical Metallurgy", "Physical metallurgy, structural alloy design, and materials characterization"),
                "GOAL_MM_PROCESS_ENGINEER": ("Process Metallurgist (Iron & Steelmaking)", "Primary extraction, blast furnace operations, and steelmaking technology")
            }
            title, desc = goal_names.get(goal_id, ("Core Engineering Track", "Core discipline engineering"))
            goal = Goal(
                goal_id=goal_id,
                name=title,
                category="career",
                description=desc,
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
