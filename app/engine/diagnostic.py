import os
import csv
import json
import random
from typing import List, Dict, Any, Optional, Tuple
from app.contracts.kb import Exercise
from app.engine.interfaces import IAdaptiveDiagnostic

def _load_default_item_bank() -> List[Exercise]:
    csv_path = os.path.join("data", "seed", "kb", "exercise.csv")
    if not os.path.exists(csv_path):
        return []
    items = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            opts_raw = r.get("options")
            options_list = []
            if opts_raw:
                try:
                    parsed = json.loads(opts_raw)
                    if isinstance(parsed, dict):
                        options_list = [f"{k}: {v}" for k, v in parsed.items()]
                    elif isinstance(parsed, list):
                        options_list = parsed
                except Exception:
                    options_list = [opts_raw]

            ans_raw = r.get("answer_key")
            correct_ans = ""
            if ans_raw:
                try:
                    parsed_ans = json.loads(ans_raw)
                    opt_letter = parsed_ans.get("correct_option", "")
                    # Match full option text if available
                    for opt in options_list:
                        if opt.startswith(f"{opt_letter}:"):
                            correct_ans = opt
                            break
                    if not correct_ans:
                        correct_ans = opt_letter
                except Exception:
                    correct_ans = ans_raw

            diff_num = float(r.get("difficulty", 2))
            diff_score = diff_num * 20.0

            items.append(Exercise(
                exercise_id=r["exercise_id"],
                skill_id=r["skill_id"],
                title=f"Question {r['exercise_id']}",
                question_text=r["prompt"],
                exercise_type="mcq" if r.get("kind") == "mcq" else "numeric",
                options=options_list,
                correct_answer=correct_ans,
                difficulty_0_100=diff_score,
                status=r.get("status", "draft_for_review"),
                source_id="AI_DRAFT",
                verified=False
            ))
    return items

class AdaptiveDiagnostic(IAdaptiveDiagnostic):
    """
    Adaptive Diagnostic Engine.
    Rules:
    1. Starts at medium difficulty (50.0).
    2. Raises difficulty (+15.0) after a correct answer; lowers difficulty (-15.0) after an incorrect answer.
    3. Requires a minimum of 5 items and terminates at a maximum of 8 items.
    4. Stops early between 5-8 items once ability estimation confidence reaches threshold (>= 0.85).
    5. Shuffles option order at serve time to eliminate option position bias while preserving answer keys.
    """
    def __init__(
        self,
        item_bank: Optional[List[Exercise]] = None,
        min_items: int = 5,
        max_items: int = 8,
        confidence_threshold: float = 0.85,
        rng: Optional[random.Random] = None
    ):
        self.item_bank = item_bank if item_bank is not None else _load_default_item_bank()
        self.min_items = min_items
        self.max_items = max_items
        self.confidence_threshold = confidence_threshold
        self.rng = rng

    @staticmethod
    def shuffle_exercise_options(exercise: Exercise, rng: Optional[random.Random] = None) -> Exercise:
        """
        Shuffles MCQ option order at serve time and remaps the correct_answer.
        Prevents letter position bias while strictly preserving evaluation accuracy.
        """
        if exercise.exercise_type != "mcq" or not exercise.options:
            return exercise

        raw_opts = list(exercise.options)
        parsed_opts = []
        correct_text = None
        raw_correct = (exercise.correct_answer or "").strip()

        for opt in raw_opts:
            if ":" in opt:
                letter, text = opt.split(":", 1)
                letter = letter.strip()
                text = text.strip()
            else:
                letter = ""
                text = opt.strip()
            parsed_opts.append((letter, text))

            # Identify which text belongs to the correct answer
            if raw_correct:
                if raw_correct == letter or raw_correct.lower() == letter.lower():
                    correct_text = text
                elif raw_correct == opt or raw_correct.lower() == text.lower() or raw_correct.endswith(text):
                    correct_text = text

        if not correct_text and parsed_opts:
            correct_text = parsed_opts[0][1]

        texts = [p[1] for p in parsed_opts]
        shuffled_texts = list(texts)
        if rng:
            rng.shuffle(shuffled_texts)
        else:
            random.shuffle(shuffled_texts)

        letters = ["A", "B", "C", "D", "E", "F"][:len(shuffled_texts)]
        new_options = []
        new_correct_letter = "A"
        new_correct_answer = ""

        for l, t in zip(letters, shuffled_texts):
            new_opt_str = f"{l}: {t}"
            new_options.append(new_opt_str)
            if t == correct_text:
                new_correct_letter = l
                new_correct_answer = f"{l}: {t}"

        return Exercise(
            exercise_id=exercise.exercise_id,
            skill_id=exercise.skill_id,
            course_id=exercise.course_id,
            title=exercise.title,
            question_text=exercise.question_text,
            exercise_type=exercise.exercise_type,
            options=new_options,
            correct_answer=new_correct_answer or new_correct_letter,
            difficulty_0_100=exercise.difficulty_0_100,
            status=exercise.status,
            source_id="AI_DRAFT",
            verified=exercise.verified
        )

    def estimate_ability_and_confidence(self, previous_answers: List[Dict[str, Any]]) -> Tuple[float, float]:
        if not previous_answers:
            return 50.0, 0.0

        n = len(previous_answers)
        correct_count = sum(1 for a in previous_answers if a.get("is_correct"))

        difficulties = [float(a.get("difficulty", 50.0)) for a in previous_answers]
        avg_diff = sum(difficulties) / n
        accuracy = correct_count / n
        ability = max(10.0, min(95.0, avg_diff + (accuracy - 0.5) * 30.0))

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

        if not previous_answers:
            target_diff = 50.0
        else:
            last_ans = previous_answers[-1]
            last_diff = float(last_ans.get("difficulty", 50.0))
            if last_ans.get("is_correct"):
                target_diff = min(95.0, last_diff + 15.0)
            else:
                target_diff = max(15.0, last_diff - 15.0)

        best_item = None
        best_diff_gap = 999.0

        for ex in self.item_bank:
            if ex.exercise_id not in asked_exercise_ids and ex.skill_id in candidate_skills:
                gap = abs(ex.difficulty_0_100 - target_diff)
                if gap < best_diff_gap:
                    best_diff_gap = gap
                    best_item = ex

        if not best_item:
            next_idx = len(previous_answers) + 1
            skill = candidate_skills[(next_idx - 1) % len(candidate_skills)] if candidate_skills else "SKILL_CIRCUIT_ANALYSIS"
            best_item = Exercise(
                exercise_id=f"DIAG_EX_{next_idx}",
                skill_id=skill,
                title=f"Diagnostic Question {next_idx} on {skill}",
                question_text=f"Adaptive diagnostic item evaluating proficiency in {skill}.",
                exercise_type="mcq",
                options=["A: Option Alpha", "B: Option Beta", "C: Option Gamma", "D: Option Delta"],
                correct_answer="A: Option Alpha",
                difficulty_0_100=target_diff,
                status="draft_for_review",
                source_id="AI_DRAFT",
                verified=False
            )

        return self.shuffle_exercise_options(best_item, self.rng)

    def is_complete(self, previous_answers: List[Dict[str, Any]]) -> bool:
        n = len(previous_answers)
        if n < self.min_items:
            return False
        if n >= self.max_items:
            return True
        _, confidence = self.estimate_ability_and_confidence(previous_answers)
        return confidence >= self.confidence_threshold


