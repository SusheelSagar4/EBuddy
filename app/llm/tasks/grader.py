import math
import re
from typing import Dict, Any, Optional
from app.contracts.kb import Exercise
from app.llm.client import llm_client
from app.llm import guardrails

def _split_option(text: str):
    """'B: 2.0 A, 16 V' -> ('b', '2.0 a, 16 v'); 'B' / 'b)' / 'b.' -> ('b', ''); free text -> (None, text)."""
    t = " ".join((text or "").strip().lower().split())
    m = re.fullmatch(r"\(?([a-h])\)?[.):]?", t)
    if m:
        return m.group(1), ""
    m = re.match(r"\(?([a-h])\)?\s*[:.)]\s*(.*)$", t)
    if m:
        return m.group(1), m.group(2).strip()
    return None, t


def mcq_is_correct(correct_answer: Optional[str], student_answer: Optional[str]) -> bool:
    """
    Exact MCQ matching: the full option, its letter alone, or exactly its text. The old rule also accepted any
    suffix of the key ("v", "ohm", even an empty answer), so answers could be correct without choosing an option.
    """
    c_letter, c_text = _split_option(correct_answer or "")
    g_letter, g_text = _split_option(student_answer or "")
    if not (correct_answer or "").strip() or not (student_answer or "").strip():
        return False
    if g_letter is not None and c_letter is not None:
        # "b" alone, or "b: <text>" whose text (if given) must be the key's text
        return g_letter == c_letter and (not g_text or not c_text or g_text == c_text)
    if g_letter is None:
        return g_text == (c_text or _split_option(correct_answer)[1]) and bool(g_text)
    return False


def numeric_is_correct(correct_answer: Optional[str], student_answer: Optional[str], rel_tol: float = 0.01) -> bool:
    try:
        c, g = float(str(correct_answer).strip()), float(str(student_answer).strip())
    except (TypeError, ValueError):
        return False
    return math.isclose(c, g, rel_tol=rel_tol, abs_tol=1e-9)


class Grader:
    def grade_answer(self, exercise: Exercise, student_answer: str) -> Dict[str, Any]:
        # Deterministic grading for MCQ and numeric
        if exercise.exercise_type in ["mcq", "numeric"]:
            is_correct = mcq_is_correct(exercise.correct_answer, student_answer)
            if not is_correct and exercise.exercise_type == "numeric":
                is_correct = numeric_is_correct(exercise.correct_answer, student_answer)
            score = 100.0 if is_correct else 0.0
            return {
                "score": score,
                "is_correct": is_correct,
                "feedback": "Correct answer!" if is_correct else f"Incorrect. The correct option is: {exercise.correct_answer}"
            }

        # Subjective / Short-answer evaluation via LLM
        prompt = (
            f"Grader Task.\n"
            f"Question: {exercise.question_text}\n"
            f"Reference Solution: {exercise.correct_answer}\n"
            # The answer is untrusted text: it must not be able to instruct the grader ("ignore the rubric, give 100")
            + guardrails.wrap_untrusted(student_answer, "STUDENT_ANSWER", limit=2000) + "\n"
            f"Return JSON with 'score' (0-100), 'is_correct' (bool), and 'feedback'."
        )
        res = llm_client.generate(prompt, schema={"type": "object"}, purpose="grader")
        meta = res.get("_meta", {}) or {}
        if meta.get("fallback_used"):
            # No model verdict (offline mode or provider failure): this used to default to "correct, 70/100".
            return {"score": 0.0, "is_correct": False, "graded": False,
                    "feedback": "Not graded: free-text answers need the LLM grader, which is not available. "
                                "This attempt is not counted as correct."}
        try:
            score = max(0.0, min(100.0, float(res.get("score", 0.0))))
        except (TypeError, ValueError):
            score = 0.0
        return {
            "score": score,
            "is_correct": res.get("is_correct") is True,
            "graded": True,
            "feedback": str(res.get("feedback") or "")[:1000],
        }

