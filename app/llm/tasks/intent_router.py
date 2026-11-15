import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.contracts.chat import Intent, ContextCard
from app.contracts.goal import canonicalize_goal_id
from app.kb.repositories import GoalRepo
from app.llm.client import llm_client
from app.engine.intent_router_fallback import keyword_fallback_route_goal

logger = logging.getLogger("ebuddy.intent_router")

class GoalAlternative(BaseModel):
    goal_id: str
    name: str
    category: str

class GoalIntakeResult(BaseModel):
    raw_query: str
    goal_id: str
    goal_name: str
    category: str
    confidence: float
    confirmation_sentence: str
    requires_confirmation: bool = True
    alternatives: List[GoalAlternative] = []

class IntentRouter:
    """
    Two-mode Intent Router:
    1. Chat message intent classifier (plan_query, domain_concept, etc.)
    2. Goal text box intake mapper to verified kb.goal ids with confirmation
    """
    def __init__(self):
        self.goal_repo = GoalRepo()

    def classify_intent(self, user_message: str, card: ContextCard) -> Intent:
        prompt = (
            f"Classify Intent Task.\n"
            f"Student Message: '{user_message}'\n"
            f"Context: Student in sem {card.current_semester}, Goal: {card.goal_name}\n"
            f"Return JSON with key 'intent' from: [plan_query, domain_concept, goal_change, diagnostic_request, progress_check, clarification, off_topic]"
        )
        res = llm_client.generate(prompt, schema={"type": "object", "properties": {"intent": {"type": "string"}}}, purpose="intent_router")
        raw_intent = res.get("intent", "plan_query").lower()
        
        for member in Intent:
            if member.value == raw_intent:
                return member
        return Intent.PLAN_QUERY

    def route_goal_text(
        self,
        user_text: str,
        programme_id: Optional[str] = None
    ) -> GoalIntakeResult:
        """
        Maps free text from the goal intake box to a verified kb.goal id.
        Uses LLM with deterministic keyword fallback.
        Validates output strictly against verified kb.goal rows.
        """
        all_goals = {g.goal_id: g for g in self.goal_repo.list_all()}
        valid_goal_ids = list(all_goals.keys())

        # Attempt LLM Classification
        prompt = (
            f"You are the Goal Intent Classifier for IIT Bhubaneswar students.\n"
            f"Student Programme: {programme_id or 'BTECH_EE'}\n"
            f"Student Goal Input: \"{user_text}\"\n"
            f"Available Goal IDs: {valid_goal_ids}\n\n"
            f"Classify the student's text to the single best goal_id from the list.\n"
            f"Return JSON with keys: goal_id (string), confidence (float between 0.0 and 1.0), reasoning (string)."
        )
        schema = {
            "type": "object",
            "properties": {
                "goal_id": {"type": "string"},
                "confidence": {"type": "number"},
                "reasoning": {"type": "string"}
            },
            "required": ["goal_id", "confidence"]
        }

        matched_goal_id = None
        confidence = 0.0

        try:
            res = llm_client.generate(prompt, schema=schema, purpose="goal_intake_router")
            candidate = res.get("goal_id", "").strip()
            conf = float(res.get("confidence", 0.0))
            if candidate in all_goals:
                matched_goal_id = candidate
                confidence = conf
        except Exception as e:
            logger.debug(f"LLM goal intake routing skipped/failed: {e}")

        # Fallback to deterministic keyword engine if LLM returned invalid or low confidence
        if not matched_goal_id or confidence < 0.5:
            fallback = keyword_fallback_route_goal(user_text, programme_id)
            matched_goal_id = fallback["goal_id"]
            confidence = fallback["confidence"]
            alt_ids = fallback["alternatives"]
        else:
            alt_ids = [gid for gid in valid_goal_ids if gid != matched_goal_id][:3]

        # Canonicalize goal id
        canonical_id = canonicalize_goal_id(matched_goal_id)
        if canonical_id not in all_goals:
            # Fallback to power / process core
            canonical_id = "GOAL_MM_PROCESS_ENGINEER" if (programme_id and "MM" in programme_id.upper()) else "GOAL_EE_CORE_POWER"

        goal_obj = all_goals[canonical_id]
        goal_name = goal_obj.name

        # Enrich alternatives
        alternatives: List[GoalAlternative] = []
        for aid in alt_ids:
            caid = canonicalize_goal_id(aid)
            if caid in all_goals and caid != canonical_id and caid not in [a.goal_id for a in alternatives]:
                a_obj = all_goals[caid]
                alternatives.append(GoalAlternative(
                    goal_id=a_obj.goal_id,
                    name=a_obj.name,
                    category=a_obj.category
                ))
            if len(alternatives) >= 3:
                break

        confirmation_sentence = f"I understood your goal as {goal_name}. Is that right?"

        return GoalIntakeResult(
            raw_query=user_text,
            goal_id=canonical_id,
            goal_name=goal_name,
            category=goal_obj.category,
            confidence=round(confidence, 2),
            confirmation_sentence=confirmation_sentence,
            requires_confirmation=True,
            alternatives=alternatives
        )

intent_router = IntentRouter()
