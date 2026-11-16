import uuid
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.contracts.chat import Intent, ContextCard, ChatTurn
from app.llm.tasks.intent_router import IntentRouter
from app.llm.tasks.explainer import Explainer
from app.llm import guardrails
from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service
from app.services.plan_service import plan_service
from app.kb.core_to_core_repo import core_kb_repo
from app.kb.repositories import CourseRepo, RuleRepo

class ChatService:
    """
    Intelligent Conversational Agent for IIT Bhubaneswar Learning Buddy.
    
    Hard constraints:
    - Pinned Context: Keeps student profile, semester, CGPA, target goal, plan version, and credit caps pinned.
    - Side Questions: Answers conceptual or institutional questions without losing plan state or conversational context.
    - Long-Term Memory: Tracks user history, preferences, and prior explanations across turns.
    - Prompt Injection Handling: Detects and neutralizes prompt injections from user input or external text.
    - Off-Topic Refusal: Politely refuses off-topic requests and steers back to core academic goals.
    """
    def __init__(self):
        self.router = IntentRouter()
        self.explainer = Explainer()
        self.course_repo = CourseRepo()
        self.rule_repo = RuleRepo()
        self.history: Dict[str, List[ChatTurn]] = {}
        self.long_term_preferences: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _second_paper_summary() -> str:
        """Allowed second papers as stored in data/seed/core_to_mtech/exam_papers.csv (never typed in by hand)."""
        try:
            from app.kb.core_to_mtech_repo import core_to_mtech_repo
            parts = [f"{code}: {p.allowed_second_papers}" for code, p in sorted(core_to_mtech_repo.exam_papers.items())
                     if p.allowed_second_papers]
            return "; ".join(parts) if parts else "none recorded"
        except Exception:
            return "not available"

    def _build_pinned_context(self, student_id: str) -> Dict[str, Any]:
        student = onboarding_service.students.get(student_id)
        goal = onboarding_service.goals.get(student_id)
        plan = plan_service.get_plan(student_id)
        states = diagnostic_service.skill_states.get(student_id, [])

        weak_skills = [
            {"skill_id": s.skill_id, "score": s.estimated_level} 
            for s in states if s.estimated_level < 75.0
        ]

        from app.kb.core_to_mtech_repo import core_to_mtech_repo
        from app.engine.gate_planner import gate_planner_engine
        from app.engine.gate_readiness_shortlist import gate_readiness_shortlist_engine

        dept = student.programme_id if student else "BTECH_EE"
        paper_code = "EE" if "EE" in dept else "MT"
        weeks_rem = gate_planner_engine.compute_weeks_remaining("2027")

        # Verified deadlines
        verified_deadlines = [
            {"event": "GATE 2027 Registration", "date": "2026-10-11", "verified": False},
            {"event": "GATE 2027 Admit Card", "date": "2027-01-08", "verified": False},
            {"event": "GATE 2027 Exam", "date": "2027-02-06", "verified": False}
        ]

        return {
            "student_id": student_id,
            "name": student.name if student else "Student",
            "programme_id": dept,
            "current_semester": student.current_semester if student else 5,
            "cgpa": student.cgpa if student else 7.5,
            "backlogs": student.backlogs if student else 0,
            "goal_id": goal.goal_id if goal else "GOAL_EE_CORE_POWER",
            "goal_name": goal.name if goal else "Core Higher Studies & GATE Track",
            "plan_version": plan.version if plan else 1,
            "active_weak_skills": weak_skills,
            "target_gate_paper": paper_code,
            "target_gate_cycle": "2027",
            "weeks_remaining": weeks_rem,
            # The fields below are fixed placeholders of the legacy chat, not computed for this student.
            "weekly_budget_hours": 15.0,
            "current_phase": "Phase 1: Foundation & High-Weightage Core",
            "readiness_status": "Assessment in progress (need >= 3 full mocks)",
            "predicted_score_band": "Not enough evidence yet (< 2 full mocks)",
            "shortlist_summary": "Not computed in this chat; open the Core to M.Tech screen for your shortlist",
            "placeholder_fields": ["weekly_budget_hours", "current_phase", "readiness_status", "next_deadlines"],
            "next_deadlines": verified_deadlines,
            "institutional_rules": [
                "RULE_SEM_CREDIT_CAP_REGULAR: 26 credits per regular semester (unsourced baseline, warning only)",
                "RULE_CGPA_PROTECTION: Priority review when score < 75% or during exam weeks"
            ]
        }

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
            {"fact": "Programme Curriculum", "value": f"B.Tech {student.programme_id if student else 'EE'} IIT BBS Official Sheet", "verified": True},
            {"fact": "Credit Cap Rule", "value": "Regular Semester Credit Cap: 26 credits (unsourced baseline)", "verified": False}
        ]
        unverified_advisories = [
            {"advisory": "Examination Schedule", "value": "Subject to formal Academic Section notification", "verified": False}
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

    def is_prompt_injection(self, text: str) -> bool:
        """Deterministic prompt-injection screen (shared implementation in app/llm/guardrails.py)."""
        return guardrails.screen_message(text)["category"] == "prompt_injection"

    def is_off_topic(self, text: str) -> bool:
        """Deterministic off-topic / integrity screen (shared implementation in app/llm/guardrails.py)."""
        return guardrails.screen_message(text)["category"] in ("off_topic", "academic_integrity", "too_long")

    def handle_side_question(self, student_id: str, message: str, pinned: Dict[str, Any]) -> Optional[str]:
        """
        Handles side questions regarding curriculum courses, professors, research areas, or academic rules
        without disrupting the active plan.
        """
        msg_upper = message.upper()

        # 1. Course lookup side question (e.g., "What is EE2L001?"). A printed code can name two courses
        #    (ML4L001-ML4L003), so every course behind each code is described, each with its notes.
        from app.kb.course_notes import course_notes
        found: List[str] = []
        for code in dict.fromkeys(re.findall(r"\b[A-Z]{2}\d[A-Z]\d{3}(?:_[A-Z]+)?\b", msg_upper)):
            for cid in course_notes.resolve(code):
                if cid in self.course_repo._courses and cid not in found:
                    found.append(cid)
        if found:
            blocks = []
            for cid in found:
                cinfo = self.course_repo._courses[cid]
                lines = [f"**Course Information ({cinfo.display_code} - {cinfo.title}):**",
                         f"- **Credits:** {cinfo.credits} | **L-T-P:** {cinfo.ltp or 'not recorded'}",
                         f"- **Level:** {cinfo.level} | **Mode:** {cinfo.mode.capitalize()}"]
                lines += [f"- **Note:** {n['text']}" for n in course_notes.notes_for(cid)]
                blocks.append("\n".join(lines))
            return ("\n\n".join(blocks) +
                    f"\n\n*(This was a side inquiry. Your active Version {pinned['plan_version']} study plan remains unchanged.)*")

        # 2. Faculty lookup side question (e.g., "Tell me about Dr. Abhik Jana")
        msg_lower = message.lower()
        for fid, fac in core_kb_repo.faculty.items():
            if fac.name.lower() in msg_lower or fid.lower() in msg_lower:
                areas = [core_kb_repo.research_areas[fa.area_id].name for fa in core_kb_repo.get_faculty_areas(fac.id) if fa.area_id in core_kb_repo.research_areas]
                area_str = ", ".join(areas) if areas else "Core Department Research"
                return (
                    f"**Faculty Profile - {fac.name}:**\n"
                    f"- **Designation:** {fac.designation} | **Department:** {fac.department}\n"
                    f"- **Lab:** {fac.lab_name or 'Department Research Facility'}\n"
                    f"- **Research Areas:** {area_str}\n"
                    f"- **UG Mentorship:** {fac.takes_ug_students.capitalize()}\n"
                    f"- **Profile:** {fac.profile_url}\n\n"
                    f"*(Your current study roadmap remains active. Would you like to check readiness criteria to approach this faculty?)*"
                )

        # 3. Academic rule side question (e.g., "credit limit", "backlogs")
        if any(kw in msg_lower for kw in ["credit cap", "maximum credit", "credit limit", "how many credits"]):
            return (
                "**Credit cap (RULE_SEM_CREDIT_CAP_REGULAR) [WARNING: unsourced_baseline]:**\n"
                "The planner uses a baseline of 26 credits per regular semester. This value has not been confirmed "
                "against the official IIT Bhubaneswar UG regulations, so plans that exceed it get a labelled warning, not a hard block. "
                "Check the current limit and the overload procedure with the Academic Section.\n\n"
                f"*(Any credit limit you set yourself is enforced as a hard limit in your plan for {pinned['goal_name']}.)*"
            )

        # 4. MBA Section & Exam Side Questions (e.g. "What is DILR?", "What is VARC?", "Explain CAT")
        if "DILR" in msg_upper or "DATA INTERPRETATION" in msg_upper or "LOGICAL REASONING" in msg_upper:
            return (
                "**MBA Entrance Section - Data Interpretation & Logical Reasoning (DILR):**\n"
                "- **CAT Format:** 20–22 questions, 40-minute sectional limit, ~4 multi-part caselet sets.\n"
                "- **Syllabus:** Matrix arrangements, scheduling, tournaments, tables, graphs, Venn diagrams.\n"
                "- **Engineering Advantage:** Engineers excel by scanning all sets in the first 5 minutes (MBA-L4) "
                "and systematically setting up constraint grids. Aim for high accuracy on 2-3 sets rather than rushing all.\n\n"
                "*(Your active prep plan tracks DILR sets without rigid timetables.)*"
            )
        if "VARC" in msg_upper or "VERBAL ABILITY" in msg_upper or "READING COMPREHENSION" in msg_upper:
            return (
                "**MBA Entrance Section - Verbal Ability & Reading Comprehension (VARC):**\n"
                "- **CAT Format:** 24 questions, 40-minute sectional limit (16 RC questions across 4 passages, 8 VA questions).\n"
                "- **Syllabus:** Dense passages from philosophy, sociology, economics; para-summaries, para-jumbles, odd-sentence-out.\n"
                "- **Verbal-Gap Strategy (MBA-L1):** 45 minutes of daily editorial reading with one-line summaries to build reading speed and argument retention.\n\n"
                "*(Your active plan allocates focused reading hours to protect your verbal percentile.)*"
            )
        if "QA" in msg_upper or "QUANTITATIVE APTITUDE" in msg_upper:
            return (
                "**MBA Entrance Section - Quantitative Aptitude (QA):**\n"
                "- **CAT Format:** 22 questions, 40-minute sectional limit.\n"
                "- **Syllabus:** Arithmetic (Percentages, Profit/Loss, TSD, Work), Algebra, Number Systems, Geometry, Modern Maths.\n"
                "- **Strategy:** As an engineering student, Quant serves as your confidence-builder. Focus on speed drills and question selection, avoiding over-practising concepts you have already mastered."
            )

        # 5. MBA Institution & Cutoff Side Questions (e.g. "IIM Ahmedabad cutoff", "Tell me about FMS")
        from app.kb.core_to_mba_repo import core_to_mba_repo
        for pid, prog in core_to_mba_repo.programmes.items():
            inst = core_to_mba_repo.institutions.get(prog.institution_id)
            inst_name = inst.name.lower() if inst else ""
            if pid.lower() in msg_lower or prog.programme_name.lower() in msg_lower or (inst_name and inst_name in msg_lower) or (inst and inst.city.lower() in msg_lower and "mba" in msg_lower):
                cutoffs = [
                    f"{s.category}: {s.cutoff_value} {s.cutoff_type}" 
                    for s in core_to_mba_repo.admission_stats 
                    if s.programme_id == prog.id and s.verified
                ]
                cutoff_str = ", ".join(cutoffs) if cutoffs else "See official notification"
                return (
                    f"**Verified B-School Programme Profile ({prog.programme_name} - {inst.name if inst else prog.institution_id}):**\n"
                    f"- **Duration:** {prog.duration_months} months | **Exams Accepted:** {prog.exams_accepted}\n"
                    f"- **Work-Ex Policy:** {prog.work_ex_policy}\n"
                    f"- **Selection Process:** {prog.selection_process}\n"
                    f"- **Application Deadline:** {prog.application_deadline or 'Check official cycle'}\n"
                    f"- **Verified Cut-offs (2024):** {cutoff_str}\n"
                    f"- **Official Website:** {prog.official_url}\n\n"
                    "*(All details sourced strictly from verified institutional records. Reach/Target/Safe tiering compares these against your calibrated mock evidence.)*"
                )

        # 6. Core-to-Management Career Path Side Questions
        for cpid, cp in core_to_mba_repo.career_paths.items():
            if cp.name.lower() in msg_lower or cpid.lower() in msg_lower:
                return (
                    f"**Core-to-Management Career Path: {cp.name} ({cp.branch}):**\n"
                    f"- **Overview:** {cp.description}\n"
                    f"- **Typical Roles:** {cp.typical_roles}\n"
                    f"- **Skills Valued:** {cp.skills_valued}\n"
                    f"- **Key Sectors:** {cp.sectors}\n"
                    f"- **Faculty Reviewer:** {cp.reviewed_by}\n\n"
                    "*(Note: Salary and placement figures are never quoted without verified institutional audit.)*"
                )
        # 7. Higher Studies & GATE side questions (§11)
        if "what is coap" in msg_lower or "coap portal" in msg_lower:
            return (
                "**Common Offer Acceptance Portal (COAP):**\n"
                "COAP is a unified web portal for graduates with valid GATE scores to view and accept admission offers "
                "for M.Tech, MS(Research), and PhD programmes from participating IITs and IISc Bangalore.\n"
                "- **Participating Institutes:** 23 IITs + IISc Bangalore\n"
                "- **Rounds:** Typically 5 main rounds (May–June) + additional spot rounds\n"
                "- **Official URL:** https://coap.iitm.ac.in/\n\n"
                f"*(This was a side inquiry. Your active Version {pinned['plan_version']} study plan remains unchanged.)*"
            )

        if "what is ccmt" in msg_lower or "ccmt portal" in msg_lower:
            return (
                "**Centralized Counselling for M.Tech/M.Arch/M.Plan (CCMT):**\n"
                "CCMT is the centralized admission portal for postgraduate engineering programmes across all NITs, "
                "IIEST Shibpur, and centrally-funded technical institutes (CFTIs).\n"
                "- **Admission Basis:** Normalized GATE scores\n"
                "- **Official URL:** https://ccmt.admissions.nic.in/\n\n"
                f"*(This was a side inquiry. Your active Version {pinned['plan_version']} study plan remains unchanged.)*"
            )

        if "allowed second paper" in msg_lower or "two paper" in msg_lower or "second paper" in msg_lower:
            return (
                "**GATE two-paper combinations [not verified]:**\n"
                f"- **Second papers in this knowledge base:** {self._second_paper_summary()}.\n"
                "- These rows are sample data and have not been checked against the official GATE 2027 brochure. "
                "Confirm the allowed combinations on the organising institute's GATE website before registering.\n\n"
                f"*(Your active target paper is {pinned.get('target_gate_paper', 'EE')}. Preparing a second paper requires balanced hours budgeting.)*"
            )

        return None

    def handle_message(self, student_id: str, message: str) -> Dict[str, Any]:
        onboarding_service.ensure_student_onboarded(student_id)  # real profile, or StudentNotFoundError
        pinned = self._build_pinned_context(student_id)
        card = self._build_context_card(student_id)

        # 1. Prompt Injection and Security Guard
        if self.is_prompt_injection(message):
            intent = Intent.OFF_TOPIC
            resp_text = (
                "Safety Notice: I am your dedicated academic learning buddy for IIT Bhubaneswar. "
                "I operate strictly under institutional rules and cannot bypass instructions, execute prompt overrides, "
                "or reveal internal system instructions. "
                f"Let's focus on your degree courses, skill roadmaps, and preparations for {pinned['goal_name']}."
            )
            side_question = False

        # 2. Off-Topic Refusal
        elif self.is_off_topic(message):
            intent = Intent.OFF_TOPIC
            resp_text = (
                "I am your academic learning buddy for IIT Bhubaneswar. "
                f"I specialize in guiding your coursework, skill development, and career pathways in {pinned['programme_id']}. "
                "I cannot assist with creative writing, games, or non-academic topics. "
                f"Would you like to review your active weekly focus items for {pinned['goal_name']} or practice a diagnostic check-in?"
            )
            side_question = False

        # 3. Side Questions (Curriculum, Faculty, or Academic Regulations)
        else:
            side_ans = self.handle_side_question(student_id, message, pinned)
            if side_ans:
                intent = Intent.PLAN_QUERY
                resp_text = side_ans
                side_question = True
            else:
                side_question = False
                intent = self.router.classify_intent(message, card)

                if intent == Intent.PLAN_QUERY:
                    plan = plan_service.get_plan(student_id)
                    explanation = self.explainer.explain_recommendation("your current curriculum plan", card)
                    resp_text = (
                        f"**Current Study Plan (Version {pinned['plan_version']}):**\n\n"
                        f"{explanation.short_summary}\n\n"
                        f"**Rationale:** {explanation.detailed_rationale}\n\n"
                        f"*Academic Rule Compliance:* Checks prerequisites and your own credit limit as hard rules; the 26-credit "
                        f"semester cap is an unsourced baseline and only raises a labelled warning."
                    )
                elif intent == Intent.GOAL_CHANGE:
                    resp_text = (
                        "Understood. If you wish to switch tracks (e.g. from Core Research to Core Industry / PSU), "
                        "I will recalibrate your required milestones and generate an updated study plan version."
                    )
                elif intent == Intent.DIAGNOSTIC_REQUEST:
                    resp_text = (
                        "You can take a short adaptive diagnostic quiz to evaluate your current skill levels. "
                        "Each answered question updates your BKT skill states and refines your roadmap."
                    )
                else:
                    resp_text = (
                        f"Received your query regarding '{message}'. "
                        f"This connects with your {pinned['goal_name']} preparation in Semester {pinned['current_semester']}."
                    )

        # 4. Long-Term Memory: Record turn and extract preferences
        turn = ChatTurn(
            turn_id=f"TURN_{uuid.uuid4().hex[:8]}",
            student_id=student_id,
            user_message=message,
            inferred_intent=intent,
            context_card=card,
            model_response=resp_text,
            plan_affected=(intent == Intent.GOAL_CHANGE),
            created_at=datetime.now(timezone.utc)
        )
        self.history.setdefault(student_id, []).append(turn)

        # Update long-term memory preferences if mentioned
        msg_l = message.lower()
        if "video" in msg_l or "nptel" in msg_l:
            self.long_term_preferences.setdefault(student_id, {})["prefers_video"] = True
        if "gate" in msg_l or "psu" in msg_l:
            self.long_term_preferences.setdefault(student_id, {})["interested_in_gate"] = True

        return {
            "turn_id": turn.turn_id,
            "inferred_intent": intent.value,
            "response": resp_text,
            "pinned_context": pinned,
            "side_question_handled": side_question,
            "disclaimer": card.disclaimer
        }

chat_service = ChatService()
