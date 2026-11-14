import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.contracts.chat import ContextCard, Intent
from app.contracts.proposal import ChangeProposal
from app.llm.tasks.intent_router import IntentRouter
from app.llm.tasks.explainer import Explainer

class QueryAdaptationAgent:
    """
    AGENT 4 — QUERY / PERSONAL ADAPTATION AGENT
    
    Responsibilities:
    1. Conversational assistant for curriculum guidance, doubts, and personal life changes.
    2. Understands student queries (e.g., "I have exams this week, reduce workload", "This resource is difficult").
    3. If query is informative/conceptual: Answers directly grounded in verified institutional data.
    4. If roadmap modification is requested: Creates a structured ChangeProposal and asks for student approval.
    5. CANNOT MODIFY ROADMAP DIRECTLY: Submits proposal to the queue; only Agent 1 can write.
    """
    def __init__(self):
        self.router = IntentRouter()
        self.explainer = Explainer()

    def handle_query(
        self,
        student_id: str,
        message: str,
        context_card: ContextCard
    ) -> Dict[str, Any]:
        """
        Processes a student query.
        Returns the assistant's grounded answer AND any created ChangeProposal requiring student approval.
        """
        msg_lower = message.lower()
        proposal: Optional[ChangeProposal] = None

        # 1. Prompt Injection and Security Guard
        if any(kw in msg_lower for kw in ["ignore previous", "system prompt", "jailbreak", "override instructions", "print your prompt"]):
            intent = Intent.OFF_TOPIC
            resp_text = (
                "Safety Notice: I am your academic learning buddy for IIT Bhubaneswar. "
                "I cannot disclose internal system prompts or bypass institutional instructions. "
                f"Let's focus on your degree courses, skill gaps, and study plan for {context_card.goal_name}."
            )
            return {
                "inferred_intent": intent.value,
                "response": resp_text,
                "proposal": None,
                "disclaimer": context_card.disclaimer
            }

        # 2. Workload / Exam Week Reduction Request -> Propose Schedule Adjustment
        if any(kw in msg_lower for kw in ["exam", "mid-sem", "midsem", "busy", "reduce workload", "less time", "30 min", "1 hour", "no time", "hackathon", "competition"]):
            intent = Intent.PLAN_QUERY
            proposal = ChangeProposal(
                proposal_id=f"PROP_WORKLOAD_{uuid.uuid4().hex[:8]}",
                student_id=student_id,
                proposer_agent="agent_4_query",
                proposal_type="workload_reduction",
                status="pending_student_approval",
                reasoning=f"Student requested workload reduction due to examination/time constraints ('{message}').",
                target_week=context_card.current_semester,
                proposed_modifications={
                    "daily_hours_target": 0.5,
                    "action": "defer_heavy_assignments_to_buffer_week",
                    "mode": "light_revision"
                },
                impact_summary="Reduces daily study workload to 30 mins/day this week and defers heavy project milestones to the post-exam buffer week.",
                created_at=datetime.now(timezone.utc)
            )
            resp_text = (
                "I understand you have examinations/time constraints this week! "
                "I have prepared a **Workload Reduction Proposal** to adjust your weekly schedule to 30 minutes of light review per day, "
                "deferring major project exercises to your post-exam buffer period.\n\n"
                "👉 *Please review the proposed adjustment above and confirm if you'd like me to apply this to your roadmap.*"
            )
            return {
                "inferred_intent": intent.value,
                "response": resp_text,
                "proposal": proposal.model_dump(),
                "disclaimer": context_card.disclaimer
            }

        # 3. Excessive Credit Load Request -> Strict Regulatory Refusal
        if any(kw in msg_lower for kw in ["credit cap", "exceed", "30 credit", "32 credit", "35 credit", "overload"]):
            intent = Intent.PLAN_QUERY
            resp_text = (
                "Regulatory Notice: Under IIT Bhubaneswar academic regulations (RULE_SEM_CREDIT_CAP_REGULAR), "
                "the regular semester credit ceiling is capped at 26 credits (normal workload 22-25 credits). "
                "Exceeding this limit is not permitted in standard registration and requires special Senate/Dean approval. "
                "I have constrained your study schedule within verified institutional credit boundaries."
            )
            return {
                "inferred_intent": intent.value,
                "response": resp_text,
                "proposal": None,
                "disclaimer": context_card.disclaimer
            }

        # 4. Standard Educational / Planning Router
        intent = self.router.classify_intent(message, context_card)

        if intent == Intent.OFF_TOPIC:
            resp_text = (
                "I am your academic learning buddy for IIT Bhubaneswar. "
                f"Let's focus on your degree courses, skill gaps, and study plan for {context_card.goal_name}. "
                "How can I assist with your coursework or preparations?"
            )
        elif intent == Intent.PLAN_QUERY:
            explanation = self.explainer.explain_recommendation("your current curriculum plan", context_card)
            resp_text = (
                f"{explanation.short_summary}\n\n"
                f"**Rationale:** {explanation.detailed_rationale}\n\n"
                f"*Strict Institutional Notice:* Unconfirmed dates or credit policies are labeled pending official notices."
            )
        elif intent == Intent.GOAL_CHANGE:
            proposal = ChangeProposal(
                proposal_id=f"PROP_GOAL_{uuid.uuid4().hex[:8]}",
                student_id=student_id,
                proposer_agent="agent_4_query",
                proposal_type="goal_pivot",
                status="pending_student_approval",
                reasoning=f"Student requested target goal modification: '{message}'.",
                proposed_modifications={
                    "requested_query": message,
                    "action": "recalibrate_skill_competencies"
                },
                impact_summary="Recalibrates target skill thresholds and generates an aligned curriculum path.",
                created_at=datetime.now(timezone.utc)
            )
            resp_text = (
                "Understood! I have created a **Goal Recalibration Proposal**. "
                "Once approved, Agent 1 will re-plan your elective choices and prerequisite sequences.\n\n"
                "👉 *Please confirm if you want to apply this target goal update.*"
            )
        else:
            resp_text = f"Received your query regarding '{message}'. Let's review how this aligns with {context_card.goal_name}."

        return {
            "inferred_intent": intent.value,
            "response": resp_text,
            "proposal": proposal.model_dump() if proposal else None,
            "disclaimer": context_card.disclaimer
        }

