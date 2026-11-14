import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone
from app.contracts.chat import Intent, ContextCard, ChatTurn
from app.llm.tasks.intent_router import IntentRouter
from app.llm.tasks.explainer import Explainer
from app.llm.client import llm_client
from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service
from app.services.plan_service import plan_service

class ChatService:
    def __init__(self):
        self.router = IntentRouter()
        self.explainer = Explainer()
        self.history: Dict[str, List[ChatTurn]] = {}

    def _build_context_card(self, student_id: str) -> ContextCard:
        student = onboarding_service.students.get(student_id)
        goal = onboarding_service.goals.get(student_id)
        plan = plan_service.get_plan(student_id)
        states = diagnostic_service.skill_states.get(student_id, [])

        plan_items = [it.model_dump() for it in plan.items] if plan else []
        skill_gaps = [
            {"skill_id": s.skill_id, "estimated_level": s.estimated_level, "confidence": s.confidence}
            for s in states
        ]

        verified_facts = [
            {"fact": "Programme Curriculum", "value": "B.Tech Electrical Engineering 2016-17 Sheet", "verified": True},
            {"fact": "Credit Cap Rule", "value": "Regular Semester Credit Cap: 16-26 credits", "verified": True}
        ]
        unverified_advisories = [
            {"advisory": "Examination Schedule", "value": "Not confirmed yet (contact Academic Section)", "verified": False},
            {"advisory": "Minor Degree Regulations", "value": "Subject to formal notification by Senate", "verified": False}
        ]

        return ContextCard(
            student_id=student_id,
            programme_id=student.programme_id if student else "BTECH_EE",
            current_semester=student.current_semester if student else 5,
            cgpa=student.cgpa if student else 7.5,
            goal_id=goal.goal_id if goal else "GOAL_EE_CORE_POWER",
            goal_name=goal.name if goal else "Power Systems & Smart Grid",
            skill_gaps=skill_gaps,
            current_plan_items=plan_items,
            verified_facts=verified_facts,
            unverified_advisories=unverified_advisories
        )

    def handle_message(self, student_id: str, message: str) -> Dict[str, Any]:
        card = self._build_context_card(student_id)
        msg_lower = message.lower()

        # 1. Prompt Injection and Security Guard
        if any(kw in msg_lower for kw in ["ignore previous", "system prompt", "jailbreak", "override instructions", "print your prompt"]):
            intent = Intent.OFF_TOPIC
            resp_text = (
                "Safety Notice: I am your academic learning buddy for IIT Bhubaneswar. "
                "I cannot disclose internal system prompts or bypass institutional instructions. "
                f"Let's focus on your degree courses, skill gaps, and study plan for {card.goal_name}."
            )
        # 2. Credit Cap Exceed Request Guard
        elif any(kw in msg_lower for kw in ["credit cap", "exceed", "30 credit", "32 credit", "35 credit", "overload"]):
            intent = Intent.PLAN_QUERY
            resp_text = (
                "Regulatory Notice: Under IIT Bhubaneswar academic regulations (RULE_SEM_CREDIT_CAP_REGULAR), "
                "the regular semester credit ceiling is capped at 26 credits (normal workload 22-25 credits). "
                "Exceeding this limit is not permitted in standard registration and requires special Senate/Dean approval. "
                "I have constrained your study schedule within verified institutional credit boundaries."
            )
        else:
            intent = self.router.classify_intent(message, card)

            if intent == Intent.OFF_TOPIC:
                resp_text = (
                    "I am your academic learning buddy for IIT Bhubaneswar. "
                    "Let's focus on your degree courses, skill gaps, and study plan for "
                    f"{card.goal_name}. How can I assist with your coursework or preparations?"
                )
            elif intent == Intent.PLAN_QUERY:
                explanation = self.explainer.explain_recommendation("your current curriculum plan", card)
                resp_text = (
                    f"{explanation.short_summary}\n\n"
                    f"**Rationale:** {explanation.detailed_rationale}\n\n"
                    f"*Strict Institutional Notice:* Unconfirmed dates or credit policies are labeled pending official notices."
                )
            elif intent == Intent.GOAL_CHANGE:
                resp_text = (
                    "Understood. If you wish to switch tracks (e.g. from Power to VLSI or SDE), "
                    "I will recalibrate your required skill competencies and generate an updated study plan."
                )
            elif intent == Intent.DIAGNOSTIC_REQUEST:
                resp_text = (
                    "You can start a short adaptive diagnostic quiz to evaluate your current skill levels. "
                    "Each answered question refines your skill estimations and updates your plan."
                )
            else:
                resp_text = f"Received your query regarding '{message}'. Let's review how this aligns with {card.goal_name}."

        turn = ChatTurn(
            turn_id=f"TURN_{uuid.uuid4().hex[:8]}",
            student_id=student_id,
            user_message=message,
            inferred_intent=intent,
            context_card=card,
            model_response=resp_text,
            plan_affected=False,
            created_at=datetime.now(timezone.utc)
        )
        self.history.setdefault(student_id, []).append(turn)

        return {
            "turn_id": turn.turn_id,
            "inferred_intent": intent.value,
            "response": resp_text,
            "disclaimer": card.disclaimer
        }

chat_service = ChatService()

