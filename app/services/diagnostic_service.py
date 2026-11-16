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
        # Items served to a student and not answered yet, with their (possibly shuffled) answer key. An answer is
        # accepted only for an item in here, and it is removed when answered: no replaying one correct answer to
        # pile up "strong" evidence, no answering items that were never served, no client-supplied answer keys.
        self.served_keys: Dict[tuple, Exercise] = {}

    def get_prior(self, student_id: str, candidate_skills: List[str]) -> Dict[str, Any]:
        return self.diagnostic_engine.prior_from_evidence(self.skill_states.get(student_id, []), candidate_skills)

    def bank_item(self, exercise_id: str) -> Optional[Exercise]:
        """The verified item-bank copy of an exercise (with the server's answer key), or None."""
        return next((ex for ex in self.diagnostic_engine.item_bank if ex.exercise_id == exercise_id), None)

    def serve(self, student_id: str, item: Exercise) -> None:
        self.served_keys[(student_id, item.exercise_id)] = item

    def take_served(self, student_id: str, exercise_id: str) -> Optional[Exercise]:
        """Returns the served item and marks it answered (one answer per serve), or None if it was not served."""
        return self.served_keys.pop((student_id, exercise_id), None)

    def get_next_question(self, student_id: str, candidate_skills: List[str]) -> Optional[Exercise]:
        answers = self.active_sessions.get(student_id, [])
        prior = self.get_prior(student_id, candidate_skills)
        item = self.diagnostic_engine.select_next_item(candidate_skills, answers, prior_difficulty=prior["start_difficulty"])
        if item is not None:
            # remember the (shuffled) answer key server-side; it is never sent to the browser
            self.serve(student_id, item)
        return item

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
            "score": score,
            "difficulty": exercise.difficulty_0_100
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
        ability, conf = self.diagnostic_engine.estimate_ability_and_confidence(session)

        return {
            "exercise_id": exercise.exercise_id,
            "score": score,
            "is_correct": is_correct,
            "feedback": result["feedback"],
            "is_diagnostic_complete": is_finished,
            "ability_estimate": ability,
            "confidence": conf,
            "answers_count": len(session),
            "skill_states": [s.model_dump() for s in updated_states]
        }

    def get_diagnostic_state(self, student_id: str) -> Dict[str, Any]:
        session = self.active_sessions.get(student_id, [])
        ability, conf = self.diagnostic_engine.estimate_ability_and_confidence(session)
        complete = self.diagnostic_engine.is_complete(session)
        return {
            "student_id": student_id,
            "answers_count": len(session),
            "min_items": self.diagnostic_engine.min_items,
            "max_items": self.diagnostic_engine.max_items,
            "ability_estimate": ability,
            "confidence": conf,
            "is_complete": complete,
            "history": session
        }

    def reset_session(self, student_id: str):
        """Starts a fresh adaptive session. The evidence ledger is append-only and is never wiped here."""
        self.active_sessions[student_id] = []
        for key in [k for k in self.served_keys if k[0] == student_id]:
            del self.served_keys[key]

    def set_ledger(self, student_id: str, evidence: List[EvidenceItem]):
        """Replaces a student's ledger (seed / DB reload) and recomputes skill states."""
        self.evidence_ledger[student_id] = list(evidence)
        self.skill_states[student_id] = self.state_updater.update_states(student_id, self.evidence_ledger[student_id])

    def add_evidence(self, student_id: str, skill_id: str, source_type: str, score: float,
                     notes: Optional[str] = None, reliability_tier: Optional[str] = None) -> EvidenceItem:
        """Appends one evidence item and recomputes the skill states (deterministic)."""
        ev = EvidenceItem(
            evidence_id=f"EV_{source_type.upper()}_{uuid.uuid4().hex[:8]}", student_id=student_id, skill_id=skill_id,
            source_type=source_type, score=float(score), reliability=1.0, attempts=1,
            recorded_at=datetime.now(timezone.utc), reliability_tier=reliability_tier, notes=notes)
        self.evidence_ledger.setdefault(student_id, []).append(ev)
        self.skill_states[student_id] = self.state_updater.update_states(student_id, self.evidence_ledger[student_id])
        return ev

    def clear_all(self):
        self.evidence_ledger.clear(); self.skill_states.clear(); self.active_sessions.clear(); self.served_keys.clear()

    def record_answer(self, student_id: str, exercise_id: str, skill_id: str, is_correct: bool, difficulty: float = 0.5) -> EvidenceItem:
        """Records one objectively graded answer as diagnostic evidence (used by the fixed-form diagnostic)."""
        session = self.active_sessions.setdefault(student_id, [])
        session.append({"exercise_id": exercise_id, "skill_id": skill_id, "is_correct": is_correct,
                        "score": 100.0 if is_correct else 0.0, "difficulty": difficulty * 100.0})
        return self.add_evidence(student_id, skill_id, "diagnostic", 100.0 if is_correct else 0.0,
                                 notes=f"Diagnostic item {exercise_id}")

diagnostic_service = DiagnosticService()

