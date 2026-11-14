from typing import List, Dict, Any
from app.contracts.goal import Goal, MasteryCriteria
from app.contracts.student import EvidenceItem
from app.engine.interfaces import IMasteryEvaluator

class MasteryEvaluator(IMasteryEvaluator):
    def evaluate_mastery(
        self,
        student_id: str,
        goal: Goal,
        criteria: MasteryCriteria,
        evidence: List[EvidenceItem]
    ) -> Dict[str, Any]:
        student_ev = [e for e in evidence if e.student_id == student_id]
        crit_params = criteria.criteria

        # 1. Minimum Skill Level Evaluation
        min_skill_level = crit_params.get("min_skill_level", 75.0)
        quiz_scores = [e.score for e in student_ev if e.source_type in ["quiz", "diagnostic", "exercise"]]
        avg_score = (sum(quiz_scores) / len(quiz_scores)) if quiz_scores else 0.0

        # 2. Required Project Milestones
        req_projects = crit_params.get("required_project_milestones", 1)
        project_count = sum(1 for e in student_ev if e.source_type == "exercise" and e.score >= 70.0)

        # 3. Timed Assessments
        req_assessments = crit_params.get("required_timed_assessments", 2)
        assessment_count = sum(1 for e in student_ev if e.source_type == "quiz")

        passed_score = avg_score >= min_skill_level
        passed_projects = project_count >= req_projects
        passed_assessments = assessment_count >= req_assessments

        # "Completed" means completed requirements/exercises
        # "Demonstrated Proficiency" means exceeding thresholds on independent projects and timed quizzes
        is_completed = len(student_ev) >= 3
        demonstrated_proficiency = passed_score and passed_projects and passed_assessments

        return {
            "student_id": student_id,
            "goal_id": goal.goal_id,
            "status": "demonstrated_proficiency" if demonstrated_proficiency else ("completed" if is_completed else "in_progress"),
            "demonstrated_proficiency": demonstrated_proficiency,
            "is_completed": is_completed,
            "metrics": {
                "average_score": round(avg_score, 2),
                "threshold_score": min_skill_level,
                "completed_projects": project_count,
                "required_projects": req_projects,
                "completed_assessments": assessment_count,
                "required_assessments": req_assessments
            },
            "evidence_count": len(student_ev)
        }

