from typing import Dict, Any
from app.contracts.chat import Intent, ContextCard
from app.llm.client import llm_client

class IntentRouter:
    def classify_intent(self, user_message: str, card: ContextCard) -> Intent:
        prompt = (
            f"Classify Intent Task.\n"
            f"Student Message: '{user_message}'\n"
            f"Context: Student in sem {card.current_semester}, Goal: {card.goal_name}\n"
            f"Return JSON with key 'intent' from: [plan_query, domain_concept, goal_change, diagnostic_request, progress_check, clarification, off_topic]"
        )
        res = llm_client.generate(prompt, schema={"type": "object", "properties": {"intent": {"type": "string"}}})
        raw_intent = res.get("intent", "plan_query").lower()
        
        # Safe mapping to Intent enum
        for member in Intent:
            if member.value == raw_intent:
                return member
        return Intent.PLAN_QUERY

