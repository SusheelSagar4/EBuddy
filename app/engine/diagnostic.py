import os
import csv
import json
from typing import List, Dict, Any, Optional
from app.contracts.kb import Exercise
from app.engine.interfaces import IAdaptiveDiagnostic

class AdaptiveDiagnostic(IAdaptiveDiagnostic):
    def __init__(self, item_bank: Optional[List[Exercise]] = None, max_items: int = 5, seed_dir: str = "data/seed/kb"):
        self.max_items = max_items
        self.item_bank = item_bank if item_bank is not None else self._load_exercises(seed_dir)

    def _load_exercises(self, seed_dir: str) -> List[Exercise]:
        ex_file = os.path.join(seed_dir, "exercise.csv")
        bank = []
        if os.path.exists(ex_file):
            with open(ex_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    opts = []
                    if r.get("options"):
                        try:
                            opts = json.loads(r["options"])
                        except Exception:
                            opts = [opt.strip() for opt in r["options"].split(",")]
                    ans_key = r.get("answer_key", "")
                    corr = ""
                    if ans_key:
                        try:
                            corr_obj = json.loads(ans_key)
                            corr = corr_obj.get("correct", "")
                        except Exception:
                            corr = ans_key
                    bank.append(Exercise(
                        exercise_id=r["exercise_id"],
                        skill_id=r["skill_id"],
                        title=f"Diagnostic on {r['skill_id']}",
                        question_text=r.get("prompt", ""),
                        exercise_type="mcq",
                        options=opts,
                        correct_answer=corr,
                        difficulty_0_100=float(r.get("difficulty", 3)) * 20.0,
                        status="verified",
                        source_id=r.get("source_id", "IITBBS_FACULTY"),
                        verified=True
                    ))
        return bank

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

    def verify_question(self, question: Exercise) -> Dict[str, Any]:
        """
        Validates generated or bank question against curriculum and assessment constraints.
        Fails if skill_id is missing, options are malformed, or answer key doesn't match options.
        """
        errors = []
        if not question.skill_id or not question.skill_id.startswith("SKILL_"):
            errors.append(f"Invalid skill_id '{question.skill_id}'. Must start with 'SKILL_'.")
        if not question.question_text or len(question.question_text.strip()) < 15:
            errors.append("Question prompt is too short (< 15 characters) or empty.")
        if not question.options or len(question.options) < 2:
            errors.append("Question must have at least 2 selectable options.")
        if question.correct_answer:
            matches_option = any(
                question.correct_answer.strip().lower() == opt.strip().lower() 
                or opt.strip().startswith(question.correct_answer[:2]) 
                for opt in (question.options or [])
            )
            if not matches_option:
                errors.append(f"Correct answer '{question.correct_answer}' does not match any provided option.")
        else:
            errors.append("Question is missing correct_answer.")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }


