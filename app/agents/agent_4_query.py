import logging
import re
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.contracts.chat import ContextCard, Intent
from app.contracts.proposal import ChangeProposal
from app.llm.tasks.intent_router import IntentRouter
from app.llm.tasks.explainer import Explainer
from app.llm.tasks.answerer import Answerer
from app.llm import guardrails

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
        self.answerer = Answerer()

    GOAL_KEYWORDS = [
        (("data analyst", "data analytics", "analyst role"), "GOAL_TRACK_DA"),
        (("machine learning", "ai/ml", "aiml", " ai ", "deep learning", "ml engineer"), "GOAL_TRACK_AIML"),
        (("sde", "software", "developer", "coding job"), "GOAL_TRACK_SDE"),
        (("mba", " cat ", "management"), "GOAL_MBA_CAT"),
        (("upsc", "civil service", "ias"), "GOAL_UPSC_CSE"),
        (("startup", "founder", "entrepreneur"), "GOAL_STARTUP_FOUNDER"),
        (("vlsi", "semiconductor"), "GOAL_EE_CORE_VLSI"),
        (("power system", "smart grid", "core power"), "GOAL_EE_CORE_POWER"),
    ]

    # Phrases that on their own ask for a lighter week.
    WORKLOAD_REQUESTS = ("reduce my workload", "reduce workload", "reduce my load", "reduce the load", "lighter", "lighten",
                         "less time", "no time", "too busy", "i'm busy", "i am busy", "too much work", "cut down", "cut back",
                         "30 min", "1 hour", "adjust my schedule", "adjust my plan", "adjust my workload", "free up time")
    # Events that justify a lighter week, and softer verbs that only count when such an event is mentioned.
    WORKLOAD_EVENTS = ("exam", "mid-sem", "midsem", "end-sem", "endsem", "hackathon", "competition", "fest", "quiz week")
    WORKLOAD_SOFT_REQUESTS = ("reduce", "adjust", "busy", "pause", "postpone", "defer", "can't cope", "less work", "less study")
    _CREDIT_AMOUNT = re.compile(r"\b(\d{2})(?:\.\d)?\s*credits?\b")

    def wants_workload_reduction(self, message: str) -> bool:
        """True only when the student asks for less work; mentioning an exam alone ("when is the GATE exam?") is not a request."""
        m = message.lower()
        if any(k in m for k in self.WORKLOAD_REQUESTS):
            return True
        return any(e in m for e in self.WORKLOAD_EVENTS) and any(k in m for k in self.WORKLOAD_SOFT_REQUESTS)

    def requested_credit_load(self, message: str) -> Optional[float]:
        """Credits the student asks to register for, when the message is an overload request; None otherwise."""
        m = message.lower()
        amounts = [float(x) for x in self._CREDIT_AMOUNT.findall(m)]
        above_cap = [a for a in amounts if a > 26.0]
        asks = any(k in m for k in ("want", "take", "register", "allow", "let me", "please", "can i", "add"))
        if "overload" in m or (above_cap and asks) or ("exceed" in m and "credit" in m and asks):
            return max(above_cap) if above_cap else 30.0
        return None

    _catalogue_codes: Optional[set] = None

    @classmethod
    def catalogue_course_codes(cls) -> set:
        """Every code a student may legitimately see (internal id, printed code, display code) from the course KB."""
        if cls._catalogue_codes is None:
            codes = set()
            try:
                from app.kb.repositories import CourseRepo
                for cid, c in CourseRepo()._courses.items():
                    codes.update(x for x in (cid, c.course_code, c.display_code) if x)
            except Exception:
                # with an empty catalogue every course code would be stripped from LLM answers
                logging.getLogger("ebuddy.agent4").exception("Course catalogue could not be loaded for answer checking")
            cls._catalogue_codes = codes
        return cls._catalogue_codes

    def detect_target_goal(self, message: str, programme_id: str) -> Optional[str]:
        """Deterministic mapping of a goal-switch request to a knowledge-base goal id (None when unclear)."""
        m = f" {message.lower()} "
        if any(k in m for k in ("higher studies", "m.tech", "mtech", "gate", "phd", "research")):
            return "GOAL_MM_RES_HIGHER_STUDIES" if "MM" in (programme_id or "") else "GOAL_EE_RES_HIGHER_STUDIES"
        for keys, gid in self.GOAL_KEYWORDS:
            if any(k in m for k in keys):
                return gid
        return None

    @staticmethod
    def _plan_item_for_course(context_card: ContextCard, message: str) -> Optional[Dict[str, Any]]:
        import re
        codes = re.findall(r"\b[A-Z]{2}\d[A-Z]\d{3}\b", message.upper())
        for code in codes:
            for it in context_card.current_plan_items:
                if it.get("course_id") == code and it.get("item_type") == "course":
                    return it
        return {"course_id": codes[0], "_not_in_plan": True} if codes else None

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
        screen = self.router.screen(message)
        if not screen["allowed"]:
            # Deterministic decline-and-redirect: the LLM is never called for blocked messages.
            return {
                "inferred_intent": Intent.OFF_TOPIC.value,
                "response": guardrails.refusal_text(screen["category"], context_card.goal_name, context_card.programme_id),
                "proposal": None,
                "guardrail": {"blocked": True, "category": screen["category"], "reason": screen["reason"]},
                "llm_used": False,
                "disclaimer": context_card.disclaimer
            }

        # 2. Workload / Exam Week Reduction Request -> Propose Schedule Adjustment
        if self.wants_workload_reduction(message):
            intent = Intent.PLAN_QUERY
            proposal = ChangeProposal(
                proposal_id=f"PROP_WORKLOAD_{uuid.uuid4().hex[:8]}",
                student_id=student_id,
                proposer_agent="agent_4_query",
                proposal_type="workload_reduction",
                status="pending_student_approval",
                reasoning=f"Student requested workload reduction due to examination/time constraints ('{message}').",
                target_week=1,
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
        requested_credits = self.requested_credit_load(message)
        if requested_credits is not None:
            intent = Intent.PLAN_QUERY
            proposal = ChangeProposal(
                proposal_id=f"PROP_OVERLOAD_{uuid.uuid4().hex[:8]}",
                student_id=student_id,
                proposer_agent="agent_4_query",
                proposal_type="credit_overload",
                status="pending_student_approval",
                reasoning=f"[WARNING: unsourced_baseline] Student requested credit overload ('{message}') exceeding baseline cap of 26.0 credits (RULE_SEM_CREDIT_CAP_REGULAR).",
                target_week=1,
                proposed_modifications={
                    "requested_credits": requested_credits,
                    "baseline_limit": 26.0,
                    "condition": "requires_official_approval_procedure_unconfirmed"
                },
                impact_summary="[WARNING: unsourced_baseline] Overload exceeds 26-credit baseline limit; recommendation subject to academic advisor confirmation.",
                created_at=datetime.now(timezone.utc)
            )
            resp_text = (
                "[WARNING: unsourced_baseline] Academic Advisory: Under IIT Bhubaneswar baseline guidelines "
                "(RULE_SEM_CREDIT_CAP_REGULAR), the regular semester credit ceiling is normally 26 credits. "
                "Because this limit originates from unverified baseline rules, I have prepared a provisional "
                "Overload Proposal for you rather than hard-blocking your request. "
                "Check the actual overload procedure (approvals, CGPA conditions) with your faculty advisor and the Academic Section.\n\n"
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
        llm_used = False

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
            item = self._plan_item_for_course(context_card, message)
            if item and not item.get("_not_in_plan"):
                # Grounded "why": quoted from the planner's own structured reason (no generation involved)
                reason = item.get("reason", {})
                rules = "; ".join(reason.get("rule_compliance", [])[:3]) or "curriculum rules checked by the validator"
                resp_text = (
                    f"**Why {item['course_id']} {item.get('title') or ''} is on your roadmap (Semester {item.get('semester_number')}):**\n"
                    f"{reason.get('why_this', 'Planned by the deterministic planner.')}\n\n"
                    f"**Rule checks:** {rules}.\n"
                    f"*Source: deterministic planner + validator; course code verified in the knowledge base.*"
                    f"{conflict_note}"
                )
            elif item and item.get("_not_in_plan"):
                resp_text = (
                    f"{item['course_id']} is not in your current roadmap. If you expected it, it may be already completed, "
                    f"an elective option that ranked lower for {context_card.goal_name}, or not in the knowledge base. "
                    f"Open the Plan screen to see the alternatives considered for each elective slot.{conflict_note}"
                )
            else:
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
                    "action": "recalibrate_skill_competencies",
                    "target_goal_id": self.detect_target_goal(message, context_card.programme_id),
                },
                impact_summary="Recalibrates target skill thresholds and generates an aligned curriculum path; completed courses and evidence are kept.",
                created_at=datetime.now(timezone.utc)
            )
            resp_text = (
                "Understood! I have created a **Goal Recalibration Proposal**. "
                "Once approved, Agent 1 will re-plan your elective choices and prerequisite sequences.\n\n"
                "👉 *Please confirm if you want to apply this target goal update.*"
                f"{conflict_note}"
            )
        elif intent == Intent.DIAGNOSTIC_REQUEST:
            resp_text = ("Open the Diagnostic screen for a short adaptive check (5-8 questions). It starts from your assessed "
                         "evidence, not from self-ratings, and every answer updates your skill state and roadmap." + conflict_note)
        elif intent == Intent.PROGRESS_CHECK:
            resp_text = ("Open the Mastery screen: it separates courses you have completed from proficiency you have demonstrated "
                         "(timed quizzes, rubric projects, mock interviews) for " + context_card.goal_name + "." + conflict_note)
        else:
            # Codes in the catalogue are real even when they are not in this plan (e.g. a prerequisite already passed);
            # only codes that exist nowhere in the knowledge base are stripped from the model's answer.
            valid_ids = {it.get("course_id") for it in context_card.current_plan_items if it.get("course_id")}
            valid_ids |= self.catalogue_course_codes()
            ans = self.answerer.answer(message, context_card, valid_ids)
            llm_used = not ans["fallback_used"]
            if ans["text"]:
                resp_text = ans["text"] + conflict_note
            else:
                focus = ", ".join(f"{g['skill_id']} ({g.get('estimated_level')})" for g in context_card.skill_gaps[:3]) or "no assessed skills yet"
                resp_text = (
                    f"I can answer from your plan and the knowledge base. For {context_card.goal_name} in Semester "
                    f"{context_card.current_semester}, your current assessed focus skills are: {focus}. "
                    f"Ask me \"why is <course code> on my roadmap\", \"what changed\", or name a course code, faculty member or rule "
                    f"for a grounded answer.{conflict_note}"
                )

        return {
            "inferred_intent": intent.value,
            "response": resp_text,
            "proposal": proposal.model_dump() if proposal else None,
            "guardrail": {"blocked": False, "category": "ok"},
            "llm_used": llm_used,
            "disclaimer": context_card.disclaimer
        }

