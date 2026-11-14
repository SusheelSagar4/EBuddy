from typing import Dict, Any, Optional
from app.contracts.kb import Exercise
from app.llm.client import llm_client

class Grader:
    def grade_answer(self, exercise: Exercise, student_answer: str) -> Dict[str, Any]:
        # Deterministic grading for MCQ and numeric
        if exercise.exercise_type in ["mcq", "numeric"]:
            correct = (exercise.correct_answer or "").strip().lower()
            given = student_answer.strip().lower()

            correct_letter = correct.split(":")[0].strip() if ":" in correct else correct
            given_letter = given.split(":")[0].strip() if ":" in given else given

            is_correct = (
                (correct == given)
                or (correct_letter == given_letter)
                or (correct.startswith(given + ":"))
                or (correct.endswith(given))
                or (given.endswith(correct))
            )
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
            f"Student Answer: {student_answer}\n"
            f"Return JSON with 'score' (0-100), 'is_correct' (bool), and 'feedback'."
        )
        res = llm_client.generate(prompt, schema={"type": "object"})
        return {
            "score": float(res.get("score", 70.0)),
            "is_correct": bool(res.get("is_correct", True)),
            "feedback": res.get("feedback", "Good effort. Review core principles.")
        }

