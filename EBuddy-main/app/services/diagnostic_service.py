import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.contracts.student import EvidenceItem, SkillState
from app.contracts.kb import Exercise
from app.engine.diagnostic import AdaptiveDiagnostic
from app.engine.skill_state import SkillStateUpdater
from app.llm.tasks.grader import Grader

class DiagnosticService:
    def __init__(self):
        self.diagnostic_engine = AdaptiveDiagnostic()
        self.state_updater = SkillStateUpdater()
        self.grader = Grader()
        self.evidence_ledger: Dict[str, List[EvidenceItem]] = {}
        self.skill_states: Dict[str, List[SkillState]] = {}
        self.active_sessions: Dict[str, List[Dict[str, Any]]] = {}

    def get_next_question(self, student_id: str, candidate_skills: List[str]) -> Optional[Exercise]:
        answers = self.active_sessions.get(student_id, [])
        return self.diagnostic_engine.select_next_item(candidate_skills, answers)

    def submit_answer(
        self,
        student_id: str,
        exercise: Exercise,
        student_answer: str
    ) -> Dict[str, Any]:
        result = self.grader.grade_answer(exercise, student_answer)
        score = result["score"]
        is_correct = result["is_correct"]

        # Record answer in active session
        session = self.active_sessions.setdefault(student_id, [])
        session.append({
            "exercise_id": exercise.exercise_id,
            "skill_id": exercise.skill_id,
            "answer": student_answer,
            "is_correct": is_correct,
            "score": score
        })

        # Append to evidence ledger
        evidence = EvidenceItem(
            evidence_id=f"EV_{uuid.uuid4().hex[:8]}",
            student_id=student_id,
            skill_id=exercise.skill_id,
            source_type="diagnostic",
            score=score,
            reliability=1.0,
            attempts=1,
            recorded_at=datetime.now(timezone.utc)
        )
        self.evidence_ledger.setdefault(student_id, []).append(evidence)

        # Update SkillState
        updated_states = self.state_updater.update_states(student_id, self.evidence_ledger[student_id])
        self.skill_states[student_id] = updated_states

        is_finished = self.diagnostic_engine.is_complete(session)

        return {
            "exercise_id": exercise.exercise_id,
            "score": score,
            "is_correct": is_correct,
            "feedback": result["feedback"],
            "is_diagnostic_complete": is_finished,
            "skill_states": [s.model_dump() for s in updated_states]
        }

diagnostic_service = DiagnosticService()

