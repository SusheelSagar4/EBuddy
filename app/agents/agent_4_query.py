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

        # 3. Credit Load Request -> Labelled Warning under unsourced_baseline rules
        if any(kw in msg_lower for kw in ["credit cap", "exceed", "30 credit", "32 credit", "35 credit", "overload"]):
            intent = Intent.PLAN_QUERY
            proposal = ChangeProposal(
                proposal_id=f"PROP_OVERLOAD_{uuid.uuid4().hex[:8]}",
                student_id=student_id,
                proposer_agent="agent_4_query",
                proposal_type="credit_overload",
                status="pending_student_approval",
                reasoning=f"[WARNING: unsourced_baseline] Student requested credit overload ('{message}') exceeding baseline cap of 26.0 credits (RULE_SEM_CREDIT_CAP_REGULAR).",
                target_week=context_card.current_semester,
                proposed_modifications={
                    "requested_credits": 30.0,
                    "baseline_limit": 26.0,
                    "condition": "requires_dean_senate_approval"
                },
                impact_summary="[WARNING: unsourced_baseline] Overload exceeds 26-credit baseline limit; recommendation subject to academic advisor confirmation.",
                created_at=datetime.now(timezone.utc)
            )
            resp_text = (
                "[WARNING: unsourced_baseline] Academic Advisory: Under IIT Bhubaneswar baseline guidelines "
                "(RULE_SEM_CREDIT_CAP_REGULAR), the regular semester credit ceiling is normally 26 credits. "
                "Because this limit originates from unverified baseline rules, I have prepared a provisional "
                "Overload Proposal for you rather than hard-blocking your request. "
                "Note that registering beyond 26 credits requires departmental advisor and Senate approval.\n\n"
                "👉 *Please review the provisional overload proposal above.*"
            )
            return {
                "inferred_intent": intent.value,
                "response": resp_text,
                "proposal": proposal.model_dump(),
                "disclaimer": context_card.disclaimer
            }

        # 4. Standard Educational / Planning Router
        intent = self.router.classify_intent(message, context_card)

        # Check if student has interest-vs-evidence conflict in their profile/plan
        conflict_note = ""
        has_conflict = False
        if context_card.current_plan_items:
            for item in context_card.current_plan_items:
                reason = item.get("reason", {})
                if "CONFLICT: Interest vs Evidence" in str(reason.get("why_this", "")):
                    has_conflict = True
                    break
        if not has_conflict and context_card.skill_gaps:
            for g in context_card.skill_gaps:
                if g.get("estimated_level", 100) < 40 and g.get("confidence", 0) > 0:
                    has_conflict = True
                    break

        if has_conflict:
            conflict_note = (
                "\n\n[Notice: Foundational Alignment] Diagnostic evidence indicates foundational gaps in your target area. "
                "Bridging exercises are scheduled to reinforce fundamentals before advanced topics."
            )

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
                f"{conflict_note}"
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
                f"{conflict_note}"
            )
        else:
            resp_text = f"Received your query regarding '{message}'. Let's review how this aligns with {context_card.goal_name}.{conflict_note}"

        return {
            "inferred_intent": intent.value,
            "response": resp_text,
            "proposal": proposal.model_dump() if proposal else None,
            "disclaimer": context_card.disclaimer
        }

