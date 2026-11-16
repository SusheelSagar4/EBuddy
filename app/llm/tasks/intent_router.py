from typing import Dict, Any
import re
from app.contracts.chat import Intent, ContextCard
from app.llm.client import llm_client
from app.llm import guardrails

_COURSE_CODE = re.compile(r"\b[A-Z]{2}\d[A-Z]\d{3}\b")


class IntentRouter:
    """
    Intent routing = deterministic guardrails first, deterministic keyword routing second,
    LLM only for the genuinely ambiguous remainder (and only its label is used, never free text).
    """

    def screen(self, user_message: str) -> Dict[str, Any]:
        """Prompt-injection / off-topic / integrity screen. No model call."""
        return guardrails.screen_message(user_message)

    def deterministic_intent(self, user_message: str):
        m = (user_message or "").lower()
        if not self.screen(user_message)["allowed"]:
            return Intent.OFF_TOPIC
        if any(k in m for k in ("switch to", "change my goal", "change goal", "switch my goal", "switch goal", "pivot to", "want to become", "move to the")):
            return Intent.GOAL_CHANGE
        if any(k in m for k in ("diagnostic", "take a quiz", "test me", "quiz me", "assess me")):
            return Intent.DIAGNOSTIC_REQUEST
        if any(k in m for k in ("my progress", "how am i doing", "mastery", "am i ready", "readiness")):
            return Intent.PROGRESS_CHECK
        if _COURSE_CODE.search(user_message or "") or any(k in m for k in (
                "roadmap", "my plan", "why is", "why was", "why did", "elective", "credit", "semester", "backlog", "schedule", "what changed")):
            return Intent.PLAN_QUERY
        if any(k in m for k in ("what is", "explain", "how does", "difference between", "define", "derive")):
            return Intent.DOMAIN_CONCEPT
        return None

    def classify_intent(self, user_message: str, card: ContextCard) -> Intent:
        det = self.deterministic_intent(user_message)
        if det is not None:
            return det
        prompt = (
            f"Classify Intent Task.\n"
            f"Student Message: '{user_message[:400]}'\n"
            f"Context: Student in sem {card.current_semester}, Goal: {card.goal_name}\n"
            f"Return JSON with key 'intent' from: [plan_query, domain_concept, goal_change, diagnostic_request, progress_check, clarification, off_topic]"
        )
        res = llm_client.generate(prompt, schema={"type": "object", "properties": {"intent": {"type": "string"}}}, purpose="intent_router",
                                  student_id=card.student_id)
        raw_intent = str(res.get("intent", "plan_query")).lower()
        for member in Intent:
            if member.value == raw_intent:
                return member
        return Intent.PLAN_QUERY
