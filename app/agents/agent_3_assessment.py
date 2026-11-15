import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.contracts.student import StudentProfile, EvidenceItem, SkillState
from app.contracts.plan import Plan
from app.contracts.kb import Exercise
from app.contracts.proposal import ChangeProposal
from app.engine.skill_state import SkillStateUpdater
from app.llm.tasks.grader import Grader
from app.llm.tasks.question_gen import QuestionGenerator

class AssessmentMasteryAgent:
    """
    AGENT 3 — ASSESSMENT / QUIZ / ASSIGNMENT AGENT
    
    Responsibilities:
    1. Generates targeted quizzes and practice assignments tailored to current weekly skills.
    2. Evaluates student submissions with detailed feedback on weak concepts and misconceptions.
    3. Updates the student's evidence ledger and recalculates SkillStates.
    4. Evaluates mastery gates.
    5. CANNOT MODIFY ROADMAP DIRECTLY: Emits structured ChangeProposals (e.g. remediation insertion)
       when mastery is insufficient, which requires student confirmation before Agent 1 commits.
    """
    def __init__(self):
        self.grader = Grader()
        self.question_gen = QuestionGenerator()
        self.state_updater = SkillStateUpdater()

    def generate_quiz(
        self,
        skill_id: str,
        current_level: float = 50.0,
        num_questions: int = 1
    ) -> List[Exercise]:
        """Generates practice problems/quizzes matched to the student's current level."""
        questions: List[Exercise] = []
        for i in range(num_questions):
            ex = self.question_gen.generate_question(skill_id, difficulty=current_level)
            questions.append(ex)
        return questions

    def evaluate_submission(
        self,
        student_id: str,
        exercise: Exercise,
        student_answer: str,
        existing_evidence: List[EvidenceItem]
    ) -> Dict[str, Any]:
        """
        Evaluates the student's solution, updates the evidence ledger,
        and computes updated skill states.
        """
        grade_result = self.grader.grade_answer(exercise, student_answer)
        score = float(grade_result.get("score", 0.0))
        is_correct = bool(grade_result.get("is_correct", False))
        feedback = grade_result.get("feedback", "")

        # Record EvidenceItem
        ev = EvidenceItem(
            evidence_id=f"EV_SUB_{uuid.uuid4().hex[:8]}",
            student_id=student_id,
            skill_id=exercise.skill_id,
            source_type="exercise" if exercise.exercise_type != "quiz" else "quiz",
            score=score,
            reliability=1.0 if exercise.exercise_type in ["mcq", "numeric"] else 0.85,
            attempts=1,
            recorded_at=datetime.now(timezone.utc)
        )
        updated_evidence = list(existing_evidence) + [ev]

        # Recalculate skill states
        new_states = self.state_updater.update_states(student_id, updated_evidence)

        # Mastery evaluation check
        demonstrated_mastery = score >= 75.0

        return {
            "score": score,
            "is_correct": is_correct,
            "feedback": feedback,
            "skill_id": exercise.skill_id,
            "demonstrated_mastery": demonstrated_mastery,
            "new_evidence_item": ev,
            "updated_states": new_states
        }

    def propose_remediation(
        self,
        student_id: str,
        skill_id: str,
        score: float,
        target_week: int,
        course_id: Optional[str] = None
    ) -> ChangeProposal:
        """
        Generates an AdaptationProposal when student performance falls below the mastery threshold.
        Strict rule: Does NOT write to the roadmap.
        """
        return ChangeProposal(
            proposal_id=f"PROP_REMED_{uuid.uuid4().hex[:8]}",
            student_id=student_id,
            proposer_agent="agent_3_assessment",
            proposal_type="remediation_insertion",
            status="pending_student_approval",
            reasoning=f"Student scored {score}% on {skill_id} (below 75% mastery threshold). Targeted reinforcement recommended.",
            target_week=target_week,
            proposed_modifications={
                "add_exercises": [
                    {
                        "exercise_id": f"EX_REMED_{skill_id}_{uuid.uuid4().hex[:4]}",
                        "skill_id": skill_id,
                        "course_id": course_id,
                        "hours": 2.0,
                        "type": "remediation_practice"
                    }
                ],
                "recommended_focus": f"Concept review and formula drill on {skill_id}"
            },
            impact_summary=f"Adds 2 hours of targeted remediation practice for {skill_id} to ensure mastery before advancing.",
            created_at=datetime.now(timezone.utc)
        )

