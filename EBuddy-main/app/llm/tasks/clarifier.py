from typing import Dict, Any, List
from app.contracts.chat import ContextCard
from app.llm.client import llm_client

class Clarifier:
    def ask_clarification(self, query: str, card: ContextCard) -> Dict[str, Any]:
        prompt = (
            f"Clarifier Task.\n"
            f"Query: {query}\n"
            f"Context: Student in Sem {card.current_semester}, Goal: {card.goal_name}\n"
            f"Return JSON with 'clarifying_question' and 'options'."
        )
        res = llm_client.generate(prompt, schema={"type": "object"})
        return {
            "clarifying_question": res.get("clarifying_question", "Could you clarify which elective area you prefer?"),
            "options": res.get("options", ["Option A", "Option B"])
        }

