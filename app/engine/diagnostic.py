import os
import csv
import json
import random
from typing import List, Dict, Any, Optional, Tuple
from app.contracts.kb import Exercise
from app.engine.interfaces import IAdaptiveDiagnostic

def _load_default_item_bank(csv_path: Optional[str] = None) -> List[Exercise]:
    if not csv_path:
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
    items.extend(_load_track_bank_items())
    return items

def _load_track_bank_items() -> List[Exercise]:
    """MCQ items of the career-track question banks (Data Analyst), mapped to knowledge-base skills."""
    out: List[Exercise] = []
    try:
        from app.kb.track_repo import TrackRepo
        repo = TrackRepo()
    except Exception:
        return out
    for t in repo.list_tracks():
        for q in t.get("questions", []):
            if q["question_type"] != "mcq" or len(q["options"]) < 2 or not q["correct_option_text"]:
                continue
            letters = ["A", "B", "C", "D", "E"]
            opts = [f"{letters[i]}: {o}" for i, o in enumerate(q["options"])]
            correct = next((o for o in opts if o.split(": ", 1)[1] == q["correct_option_text"]), None)
            if not correct:
                continue
            out.append(Exercise(
                exercise_id=q["question_id"], skill_id=q["kb_skill_id"], title=f"{t['name']} bank: {q['track_skill_name']}",
                question_text=q["stem"], exercise_type="mcq", options=opts, correct_answer=correct,
                difficulty_0_100={1: 30.0, 2: 55.0, 3: 80.0}.get(q["difficulty_num"], 50.0),
                status="draft_for_review", source_id="TRACK_DA_KB" if t["track_id"] == "da" else "AI_DRAFT", verified=False))
    return out

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
        rng: Optional[random.Random] = None,
        seed_dir: Optional[str] = None
    ):
        if item_bank is not None:
            self.item_bank = item_bank
        elif seed_dir:
            self.item_bank = _load_default_item_bank(os.path.join(seed_dir, "exercise.csv"))
        else:
            self.item_bank = _load_default_item_bank()
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
            source_id=exercise.source_id,
            verified=exercise.verified
        )

    def compute_running_ability(self, answers: List[Dict[str, Any]]) -> float:
        """
        Computes running ability estimate with CAT step adjustments.
        Initial baseline: 50.0.
        Each step size: 25.0 / (1.0 + 0.25 * k).
        Bounded within [10.0, 95.0].
        """
        theta = 50.0
        for k, a in enumerate(answers, 1):
            step = 25.0 / (1.0 + 0.25 * k)
            if a.get("is_correct"):
                theta = min(95.0, theta + step)
            else:
                theta = max(10.0, theta - step)
        return round(theta, 2)

    def estimate_ability_and_confidence(self, previous_answers: List[Dict[str, Any]]) -> Tuple[float, float]:
        if not previous_answers:
            return 50.0, 0.0

        n = len(previous_answers)
        current_ability = self.compute_running_ability(previous_answers)

        if n < 3:
            return current_ability, round(min(0.80, 0.30 + n * 0.15), 2)

        # Compute spread (range) across the last 3 running theta ability estimates
        theta_n = current_ability
        theta_n_minus_1 = self.compute_running_ability(previous_answers[:-1])
        theta_n_minus_2 = self.compute_running_ability(previous_answers[:-2])

        last_3 = [theta_n, theta_n_minus_1, theta_n_minus_2]
        spread = max(last_3) - min(last_3)

        # Confidence is derived strictly from the spread of the last 3 theta values
        # spread <= 4.0 yields confidence >= 0.84 (converged); higher spread reduces confidence
        confidence = max(0.20, min(0.95, 1.0 - (spread / 25.0)))

        return current_ability, round(confidence, 2)

    # Evidence reliability weights used for the starting point of the adaptive test (PS Section 4)
    PRIOR_TIER_WEIGHTS = {"strong": 1.0, "mixed": 1.0, "medium": 0.6, "weak": 0.0}

    def prior_from_evidence(self, skill_states: List[Any], candidate_skills: List[str]) -> Dict[str, Any]:
        """
        Starting difficulty from what is already KNOWN about the student.
        Assessed evidence (grades, earlier diagnostics, timed quizzes) sets the start; self-declared
        interest has weight 0 here - a student cannot talk their way to harder (or fewer) questions.
        """
        used, ignored, num, den = [], [], 0.0, 0.0
        for s in skill_states or []:
            if s.skill_id not in candidate_skills:
                continue
            basis = getattr(s, "evidence_basis", None) or ("weak" if s.confidence <= 0.2 else "strong")
            w = self.PRIOR_TIER_WEIGHTS.get(basis, 0.0) * max(0.0, s.confidence)
            row = {"skill_id": s.skill_id, "level": s.estimated_level, "basis": basis, "weight": round(w, 2)}
            if w > 0:
                used.append(row); num += s.estimated_level * w; den += w
            else:
                ignored.append(row)
        start = 50.0 if den == 0 else max(20.0, min(85.0, num / den))
        return {
            "start_difficulty": round(start, 1),
            "basis": "assessed evidence" if den > 0 else "no assessed evidence: neutral start at 50",
            "used": used, "ignored_self_declared": ignored,
            "rule": "strong/medium evidence weighted by confidence; self-declared evidence weight 0",
        }

    def select_next_item(
        self,
        candidate_skills: List[str],
        previous_answers: List[Dict[str, Any]],
        prior_difficulty: Optional[float] = None
    ) -> Optional[Exercise]:
        if self.is_complete(previous_answers):
            return None

        asked_exercise_ids = {a["exercise_id"] for a in previous_answers}

        if not previous_answers:
            target_diff = prior_difficulty if prior_difficulty is not None else 50.0
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
            if self.item_bank:
                # A real bank is loaded but has no item left for these skills: stop instead of inventing a question.
                return None
            # Empty bank = engine-only simulation (unit tests of the difficulty staircase): placeholder items.
            next_idx = len(previous_answers) + 1
            skill = candidate_skills[(next_idx - 1) % len(candidate_skills)] if candidate_skills else "SKILL_CIRCUIT_ANALYSIS"
            best_item = Exercise(
                exercise_id=f"DIAG_EX_{next_idx}", skill_id=skill,
                title=f"Diagnostic Question {next_idx} on {skill}",
                question_text=f"Adaptive diagnostic item evaluating proficiency in {skill}.",
                exercise_type="mcq",
                options=["A: Option Alpha", "B: Option Beta", "C: Option Gamma", "D: Option Delta"],
                correct_answer="A: Option Alpha", difficulty_0_100=target_diff,
                status="draft_for_review", source_id="AI_DRAFT", verified=False)

        return self.shuffle_exercise_options(best_item, self.rng)

    def is_complete(self, previous_answers: List[Dict[str, Any]]) -> bool:
        n = len(previous_answers)
        if n < self.min_items:
            return False
        if n >= self.max_items:
            return True

        # Stop rule: stop when n >= 5 and the range (spread) of the last 3 theta values <= 4.0
        theta_n = self.compute_running_ability(previous_answers)
        theta_n_minus_1 = self.compute_running_ability(previous_answers[:-1])
        theta_n_minus_2 = self.compute_running_ability(previous_answers[:-2])

        last_3 = [theta_n, theta_n_minus_1, theta_n_minus_2]
        spread = max(last_3) - min(last_3)

        return spread <= 4.0

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
