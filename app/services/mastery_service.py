import logging
from typing import Dict, Any
from app.contracts.goal import MasteryCriteria
from app.engine.mastery import MasteryEvaluator
from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service
from app.services.plan_service import plan_service

DEFAULT_CRITERIA = {"min_skill_level": 75.0, "required_project_milestones": 1, "required_timed_assessments": 2,
                    "timed_quiz_threshold": 70.0, "rubric_project_threshold": 70.0,
                    "required_mock_interviews": 0, "mock_interview_threshold": 65.0}


class MasteryService:
    def __init__(self):
        self.evaluator = MasteryEvaluator()

    def criteria_for(self, goal_id: str) -> MasteryCriteria:
        crit = dict(DEFAULT_CRITERIA)
        source = "DESIGN_TEAM"
        try:
            from app.personas.registry import persona_registry
            pkg = persona_registry.for_goal(goal_id)
            if pkg and isinstance(pkg.mastery, dict) and pkg.mastery.get("criteria"):
                crit.update(pkg.mastery["criteria"])
                source = f"persona:{pkg.spec.persona_id}"
        except Exception:
            logging.getLogger("ebuddy.mastery").exception("Persona mastery criteria for %s could not be loaded; using defaults", goal_id)
        return MasteryCriteria(criteria_id=f"MASTERY_{goal_id}", goal_id=goal_id, criteria=crit, status="draft_for_review", source_id=source)

    def check_mastery(self, student_id: str) -> Dict[str, Any]:
        student = onboarding_service.students.get(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not found")
        goal = onboarding_service.goals.get(student_id)
        evidence = diagnostic_service.evidence_ledger.get(student_id, [])
        plan = plan_service.get_plan(student_id)
        current = [it.course_id for it in (plan.items if plan else [])
                   if it.item_type == "course" and it.course_id and (it.semester_number or 0) == student.current_semester]
        planner = plan_service.planner
        res = self.evaluator.evaluate_mastery(
            student_id, goal, self.criteria_for(goal.goal_id), evidence,
            requirements=plan_service.requirements_for(goal.goal_id),
            skill_states=diagnostic_service.skill_states.get(student_id, []),
            completed_course_ids=onboarding_service.completed_courses.get(student_id, []),
            current_course_ids=current,
            course_skills=planner.course_skills,
            course_titles={c: i.get("title", c) for c, i in planner.course_info.items()},
            skill_names=planner.skill_names)
        res["criteria_source"] = self.criteria_for(goal.goal_id).source_id
        return res

mastery_service = MasteryService()
