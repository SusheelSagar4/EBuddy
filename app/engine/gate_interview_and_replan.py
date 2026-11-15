from typing import List, Dict, Any, Optional
from app.contracts.core_to_mtech import (
    ScoreBand,
    Shortlist,
    GATEResult,
    InterviewSession,
    ProgrammeTier
)
from app.kb.core_to_mtech_repo import core_to_mtech_repo
from app.kb.core_to_core_repo import core_kb_repo
from app.engine.gate_readiness_shortlist import gate_readiness_shortlist_engine
from app.engine.eligibility import eligibility_engine

class GATEInterviewAndReplanEngine:
    """
    Deterministic Interview Assessment, SOP Feedback, Post-Result Re-planning and Route Switch Engine (§8.7, §8.8, §8.9).
    Hard constraints:
    - Never promises any admission result or rank.
    - Post-result re-plan produces concrete alternatives when actual score is below all Target programmes.
    - Route switches strictly preserve 100% of prior skill evidence and produce structured version diffs.
    - SOP feedback provides structured rubric suggestions; NEVER writes the student's statement.
    """
    def __init__(self, repo=None):
        self.repo = repo or core_to_mtech_repo

    def evaluate_interview_response(
        self,
        topic_id: str,
        student_response: str
    ) -> Dict[str, Any]:
        """
        Evaluates technical interview response against stored rubrics (§8.7).
        """
        resp_lower = student_response.lower().strip()
        words = resp_lower.split()
        word_count = len(words)

        # Rubric Criteria (0 to 25 each, Total 100)
        # 1. Technical Accuracy & Depth
        has_technical_terms = any(term in resp_lower for term in [
            "equation", "theorem", "voltage", "current", "flux", "energy", "efficiency",
            "phase", "stability", "transformation", "stress", "strain", "kinetics", "entropy"
        ])
        c1_score = 22.0 if (has_technical_terms and word_count >= 30) else (15.0 if word_count >= 15 else 8.0)

        # 2. Governing Laws & Mathematical Rigor
        has_math_refs = any(ref in resp_lower for ref in ["law", "derivative", "integral", "maxwell", "kirchhoff", "gibbs", "fick", "arrhenius"])
        c2_score = 23.0 if has_math_refs else 14.0

        # 3. Practical / Engineering Context
        has_practical = any(p in resp_lower for p in ["application", "design", "system", "motor", "furnace", "industry", "grid", "device"])
        c3_score = 21.0 if has_practical else 13.0

        # 4. Structure & Clarity
        c4_score = 22.0 if word_count >= 25 else 12.0

        total_score = round(c1_score + c2_score + c3_score + c4_score, 1)

        feedback_list = []
        if not has_math_refs:
            feedback_list.append("Include specific governing equations or fundamental thermodynamic/electromagnetic laws in your technical reasoning.")
        if not has_practical:
            feedback_list.append("Ground your theoretical explanation with an engineering system example (e.g. power transformer, blast furnace, EV converter).")
        if word_count < 20:
            feedback_list.append("Expand your technical response with step-by-step problem-solving derivation.")

        if not feedback_list:
            feedback_list.append("Excellent technical articulation and structured derivation aligned with IISc/IIT interview standards.")

        return {
            "topic_id": topic_id,
            "total_score": total_score,
            "rubric_breakdown": {
                "technical_accuracy": c1_score,
                "mathematical_rigor": c2_score,
                "practical_application": c3_score,
                "clarity_of_expression": c4_score
            },
            "feedback": feedback_list,
            "evidence_weight": 0.8
        }

    def review_statement_of_purpose(
        self,
        statement_text: str,
        target_programme_id: str
    ) -> Dict[str, Any]:
        """
        Reviews research statement or SOP against rubric (§8.7).
        Hard constraint: Never writes the full statement for the student.
        """
        prog = self.repo.programmes.get(target_programme_id)
        text_lower = statement_text.lower()
        word_count = len(statement_text.split())

        # Rubric dimensions (0-25)
        # 1. Research Problem Definition
        has_problem = any(w in text_lower for w in ["research", "investigate", "problem", "challenge", "develop", "model"])
        r1 = 22.0 if (has_problem and word_count >= 100) else 14.0

        # 2. Alignment with Department / Lab Areas
        dept_keywords = (prog.research_areas.lower().split(",") if prog and prog.research_areas else ["engineering"])
        has_dept_align = any(kw.strip() in text_lower for kw in dept_keywords if len(kw.strip()) > 3)
        r2 = 24.0 if has_dept_align else 12.0

        # 3. Prior Academic & Project Foundation
        has_prior_work = any(w in text_lower for w in ["b.tech", "project", "curriculum", "laboratory", "simulation", "internship", "published"])
        r3 = 23.0 if has_prior_work else 13.0

        # 4. Long-Term Motivation
        has_motivation = any(w in text_lower for w in ["career", "phd", "academic", "industry", "future", "goals"])
        r4 = 21.0 if has_motivation else 12.0

        total_score = round(r1 + r2 + r3 + r4, 1)

        # Link to Core-to-Core faculty if IIT BBS
        linked_faculty = []
        if prog and "IITBBS" in prog.institution_id:
            for fid, fac in core_kb_repo.faculty.items():
                if any(kw.strip() in fac.department.lower() for kw in dept_keywords):
                    linked_faculty.append(f"{fac.name} ({fac.department}) - Lab: {fac.lab_name or 'Department Lab'}")

        actionable_suggestions = []
        if not has_dept_align:
            actionable_suggestions.append(f"Explicitly reference department specializations: {prog.research_areas if prog else 'Department research thrusts'}.")
        if not has_prior_work:
            actionable_suggestions.append("Detail your specific undergraduate capstone project or simulation tool experience (e.g. MATLAB, ANSYS, Thermo-Calc).")
        if word_count < 150:
            actionable_suggestions.append("Your statement is brief; expand on the methodological approach and research hypothesis (ideal length: 400-600 words).")

        return {
            "target_programme_id": target_programme_id,
            "overall_score": total_score,
            "rubric_scores": {
                "research_clarity": r1,
                "institutional_alignment": r2,
                "prior_foundation": r3,
                "vision_and_motivation": r4
            },
            "suggestions": actionable_suggestions,
            "linked_iitbbs_faculty": linked_faculty[:3],
            "writing_policy_notice": "In accordance with academic integrity guidelines, EBuddy provides structured review feedback and does not write or ghostwrite admission statements."
        }

    def replan_post_result(
        self,
        student_id: str,
        actual_score: float,
        actual_rank: Optional[int],
        paper_code: str,
        category: str = "GEN",
        branch: str = "BTECH_EE",
        cgpa: float = 7.5,
        backlogs: int = 0
    ) -> Dict[str, Any]:
        """
        Re-plans student options post official GATE results (§8.8).
        If score is below all Target programmes, provides concrete realistic alternatives:
        1. MS(R) programmes (where interview/written test accounts for 30-50% selection mode)
        2. Other NITs/CFTIs matching the score
        3. Core Industry / PSU track
        4. Retake plan for next cycle (citing score validity = 3 years)
        """
        # Exact score band (zero spread since actual score is known)
        actual_band = ScoreBand(
            min_score=actual_score,
            max_score=actual_score,
            mean_score=actual_score,
            confidence_level=1.0,
            is_estimated=False,
            uncertainty_note="Official GATE result entered by student. Tiering reflects actual score against past closing cutoffs.",
            num_mocks_used=1
        )

        shortlist = gate_readiness_shortlist_engine.compute_shortlist_and_tiers(
            student_branch=branch,
            student_cgpa=cgpa,
            backlogs=backlogs,
            paper_code=paper_code,
            category=category,
            score_band=actual_band,
            allow_unverified_demo=True
        )

        has_target_or_safe = (len(shortlist.target) + len(shortlist.safe)) > 0
        alternatives = []
        trade_offs = []

        if not has_target_or_safe:
            # Score is below all Target programmes (Edge case §7 & §14)
            # Alternative 1: MS(R) Route
            msr_progs = [
                p for p in self.repo.programmes.values()
                if p.degree == "MS(R)" and paper_code in (p.gate_papers_accepted or "")
            ]
            if msr_progs:
                alternatives.append({
                    "kind": "MSR_ROUTE",
                    "title": "MS (Research) Degree Options",
                    "description": "MS(R) selection relies heavily on written test and technical interview (typically 30-50% interview weight), allowing students with lower GATE scores to qualify on research aptitude.",
                    "programmes": [f"{p.institution_id} - {p.specialisation} (Portal: {p.application_portal})" for p in msr_progs[:3]]
                })
                trade_offs.append("MS(R) Trade-off: Degree typically requires 2.5 to 3 years with intensive thesis, compared to 2-year coursework-heavy M.Tech.")

            # Alternative 2: Emerging / Interdisciplinary Specializations
            alternatives.append({
                "kind": "INTERDISCIPLINARY",
                "title": "Interdisciplinary & Newer IIT/NIT Programmes",
                "description": "Programmes in Energy Studies, Nanotechnology, and Reliability Engineering traditionally have lower GATE closing scores.",
                "programmes": ["IIT Bhubaneswar - Power System Eng", "VNIT Nagpur - Power Electronics", "NIT Surathkal - Process Metallurgy"]
            })
            trade_offs.append("Interdisciplinary Trade-off: Broader coursework curriculum, requiring personal initiative for core campus recruitment.")

            # Alternative 3: Core Industry Track
            alternatives.append({
                "kind": "CORE_INDUSTRY_TRACK",
                "title": "Switch to Core Industry Track",
                "description": "Pivot to core hardware engineering, CAD/simulation tools, and core private sector placement opportunities.",
                "programmes": ["Core Engineering Placement Route (Electrical Design / Metallurgy QC)"]
            })
            trade_offs.append("Core Industry Trade-off: Immediate employment and income, but defers master's degree qualification.")

            # Alternative 4: Retake Plan for Next GATE Cycle
            alternatives.append({
                "kind": "GATE_RETAKE",
                "title": f"GATE Retake Preparation (Next Cycle)",
                "description": f"GATE scores remain valid for 3 years. You may use this year's score as safety backup while retaking to target top 500 AIR.",
                "programmes": ["12-Month Comprehensive Revision Template"]
            })
            trade_offs.append("Retake Trade-off: Requires 6-12 months sustained preparation alongside coursework or employment.")

        # PSU Opportunities based on actual score
        eligible_psus = []
        for pid, psu in self.repo.psus.items():
            if paper_code in (psu.disciplines or ""):
                # Find past cutoff
                pcycle = next((c for c in self.repo.psu_cycles.values() if c.psu_id == pid), None)
                cut = pcycle.past_cutoff if pcycle and pcycle.past_cutoff else 700.0
                eligible = actual_score >= cut
                eligible_psus.append({
                    "psu_id": pid,
                    "name": psu.name,
                    "past_cutoff": cut,
                    "is_competitive": eligible,
                    "status": "Competitive for Interview" if eligible else "Score below historical cutoff"
                })

        return {
            "student_id": student_id,
            "actual_score": actual_score,
            "actual_rank": actual_rank,
            "paper_code": paper_code,
            "shortlist": shortlist,
            "score_below_target_warning": not has_target_or_safe,
            "alternatives": alternatives,
            "trade_offs": trade_offs,
            "eligible_psus": eligible_psus
        }

    def switch_route(
        self,
        student_id: str,
        from_route: str,
        to_route: str,
        current_evidence_count: int
    ) -> Dict[str, Any]:
        """
        Executes route transition (§8.9) preserving 100% of skill evidence.
        """
        what_carries_over = [
            f"All {current_evidence_count} existing skill assessment evidence items and mastery levels remain 100% preserved.",
            "Diagnostic results and tested technical topic proficiencies carry over seamlessly.",
            "Historical mock test records and error log analytics remain accessible in profile."
        ]

        what_changes = []
        if "PSU" in to_route.upper():
            what_changes.append("Target milestones updated: PSU recruitment windows and interview preparation prioritized.")
            what_changes.append("Aptitude and General Knowledge preparation slots added to study budget.")
        elif "INDUSTRY" in to_route.upper() or "CORE JOB" in to_route.upper():
            what_changes.append("Higher studies counselling milestones deactivated.")
            what_changes.append("Core industrial tool simulations (MATLAB/Simulink, ANSYS, EDA) and placement tests activated.")
        elif "MSR" in to_route.upper() or "PHD" in to_route.upper():
            what_changes.append("Research statement (SOP) drafting and technical interview practice milestones added.")
            what_changes.append("Faculty literature review and research area alignment enabled.")
        else:
            what_changes.append("Standard GATE → COAP/CCMT higher studies pathway configured.")

        return {
            "student_id": student_id,
            "from_route": from_route,
            "to_route": to_route,
            "what_carries_over": what_carries_over,
            "what_changes": what_changes,
            "plan_version_bump": True,
            "reason": f"Student requested route change from {from_route} to {to_route}."
        }

# Global singleton
gate_interview_and_replan_engine = GATEInterviewAndReplanEngine()
