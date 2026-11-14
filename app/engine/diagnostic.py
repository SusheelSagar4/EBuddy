from typing import List, Dict, Any, Optional, Tuple
from app.contracts.kb import Exercise
from app.engine.interfaces import IAdaptiveDiagnostic

class AdaptiveDiagnostic(IAdaptiveDiagnostic):
    """
    Adaptive Diagnostic Engine.
    Rules:
    1. Starts at medium difficulty (50.0).
    2. Raises difficulty (+15.0) after a correct answer; lowers difficulty (-15.0) after an incorrect answer.
    3. Requires a minimum of 5 items and terminates at a maximum of 8 items.
    4. Stops early between 5-8 items once ability estimation confidence reaches threshold (>= 0.85).
    """
    def __init__(
        self,
        item_bank: Optional[List[Exercise]] = None,
        min_items: int = 5,
        max_items: int = 8,
        confidence_threshold: float = 0.85
    ):
        self.item_bank = item_bank or []
        self.min_items = min_items
        self.max_items = max_items
        self.confidence_threshold = confidence_threshold

    def estimate_ability_and_confidence(self, previous_answers: List[Dict[str, Any]]) -> Tuple[float, float]:
        if not previous_answers:
            return 50.0, 0.0

        n = len(previous_answers)
        correct_count = sum(1 for a in previous_answers if a.get("is_correct"))

        # Ability estimate based on average difficulty of correct items vs total
        difficulties = [float(a.get("difficulty", 50.0)) for a in previous_answers]
        avg_diff = sum(difficulties) / n
        accuracy = correct_count / n
        ability = max(10.0, min(95.0, avg_diff + (accuracy - 0.5) * 30.0))

        # Confidence starts at 0.45 and increases with items answered
        confidence = min(0.95, 0.45 + (n * 0.08))
        if n >= 3:
            last_3 = [bool(a.get("is_correct")) for a in previous_answers[-3:]]
            if all(last_3) or not any(last_3):
                confidence = min(0.95, confidence + 0.10)

        return round(ability, 2), round(confidence, 2)

    def select_next_item(
        self,
        candidate_skills: List[str],
        previous_answers: List[Dict[str, Any]]
    ) -> Optional[Exercise]:
        if self.is_complete(previous_answers):
            return None

        asked_exercise_ids = {a["exercise_id"] for a in previous_answers}

        # Medium difficulty start (50.0), dynamically adjusted based on last response
        if not previous_answers:
            target_diff = 50.0
        else:
            last_ans = previous_answers[-1]
            last_diff = float(last_ans.get("difficulty", 50.0))
            if last_ans.get("is_correct"):
                target_diff = min(95.0, last_diff + 15.0) # Raise difficulty
            else:
                target_diff = max(15.0, last_diff - 15.0) # Lower difficulty

        # Find best matching exercise in candidate skills not yet asked
        best_item = None
        best_diff_gap = 999.0

        for ex in self.item_bank:
            if ex.exercise_id not in asked_exercise_ids and ex.skill_id in candidate_skills:
                gap = abs(ex.difficulty_0_100 - target_diff)
                if gap < best_diff_gap:
                    best_diff_gap = gap
                    best_item = ex

        # If none found in item bank, return synthetic baseline item
        if not best_item:
            next_idx = len(previous_answers) + 1
            skill = candidate_skills[(next_idx - 1) % len(candidate_skills)] if candidate_skills else "SKILL_CIRCUIT_ANALYSIS"
            best_item = Exercise(
                exercise_id=f"DIAG_EX_{next_idx}",
                skill_id=skill,
                title=f"Diagnostic Question {next_idx} on {skill}",
                question_text=f"Adaptive diagnostic item evaluating proficiency in {skill}.",
                exercise_type="mcq",
                options=["A: Correct Option", "B: Distractor 1", "C: Distractor 2", "D: Distractor 3"],
                correct_answer="A: Correct Option",
                difficulty_0_100=target_diff,
                status="draft_for_review",
                source_id="DESIGN_TEAM",
                verified=False
            )

        return best_item

    def is_complete(self, previous_answers: List[Dict[str, Any]]) -> bool:
        n = len(previous_answers)
        if n < self.min_items:
            return False
        if n >= self.max_items:
            return True
        _, confidence = self.estimate_ability_and_confidence(previous_answers)
        return confidence >= self.confidence_threshold


