from typing import Dict, Any, List, Optional
from app.contracts.kb import Exercise
from app.llm.client import llm_client

class QuestionGenerator:
    def generate_question(self, skill_id: str, difficulty: float = 50.0) -> Exercise:
        prompt = (
            f"Question Generator Task.\n"
            f"Skill: {skill_id}\n"
            f"Difficulty: {difficulty}/100\n"
            f"Generate an MCQ question in JSON format with 'title', 'question_text', 'options' (4 choices), and 'correct_answer'."
        )
        res = llm_client.generate(prompt, schema={"type": "object"})
        return Exercise(
            exercise_id=f"GEN_{skill_id[:8]}_{int(difficulty)}",
            skill_id=skill_id,
            title=res.get("title", f"Practice problem on {skill_id}"),
            question_text=res.get("question_text", f"Evaluate the primary characteristics of {skill_id}."),
            exercise_type="mcq",
            options=res.get("options", ["A: Option A", "B: Option B", "C: Option C", "D: Option D"]),
            correct_answer=res.get("correct_answer", "A: Option A"),
            difficulty_0_100=difficulty,
            status="draft_for_review",
            source_id="SYNTHETIC_EXERCISE",
            verified=False
        )

