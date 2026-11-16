from typing import List, Dict, Any, Optional
from app.contracts.kb import Exercise
from app.engine.interfaces import IAdaptiveDiagnostic

class AdaptiveDiagnostic(IAdaptiveDiagnostic):
    def __init__(self, item_bank: Optional[List[Exercise]] = None, max_items: int = 5):
        self.item_bank = item_bank or []
        self.max_items = max_items

    def select_next_item(
        self,
        candidate_skills: List[str],
        previous_answers: List[Dict[str, Any]]
    ) -> Optional[Exercise]:
        if self.is_complete(previous_answers):
            return None

        asked_exercise_ids = {a["exercise_id"] for a in previous_answers}

        # Calculate current estimated ability based on previous answers
        if previous_answers:
            correct_count = sum(1 for a in previous_answers if a.get("is_correct"))
            ratio = correct_count / len(previous_answers)
            target_diff = 40.0 + (ratio * 40.0) # Scale difficulty dynamically between 40 and 80
        else:
            target_diff = 50.0

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
            skill = candidate_skills[next_idx % len(candidate_skills)] if candidate_skills else "SKILL_CIRCUIT_ANALYSIS"
            best_item = Exercise(
                exercise_id=f"DIAG_EX_{next_idx}",
                skill_id=skill,
                title=f"Diagnostic Question {next_idx} on {skill}",
                question_text=f"Sample diagnostic problem evaluating proficiency in {skill}.",
                exercise_type="mcq",
                options=["A: Correct Option", "B: Distractor 1", "C: Distractor 2", "D: Distractor 3"],
                correct_answer="A: Correct Option",
                difficulty_0_100=target_diff,
                status="draft_for_review",
                source_id="SYNTHETIC_EXERCISE",
                verified=False
            )

        return best_item

    def is_complete(self, previous_answers: List[Dict[str, Any]]) -> bool:
        # Stop rule: reached max items or high confidence (3 in a row correct or incorrect)
        if len(previous_answers) >= self.max_items:
            return True
        if len(previous_answers) >= 3:
            last_3 = [a.get("is_correct") for a in previous_answers[-3:]]
            if all(last_3) or not any(last_3):
                return True
        return False

