import os
from typing import List, Dict, Optional, Any
from app.contracts.core_to_mba import ProfileAuditRubric, ProfileAction
from app.kb.core_to_mba_repo import core_to_mba_repo

class MBAProfileAuditEngine:
    """
    Profile Audit Engine (§1.3, §7.3 & §11).
    Evaluates student profile across 6 criteria against 4-level descriptive benchmarks:
    1. Academics
    2. Projects
    3. Internships
    4. Leadership / POR
    5. Extracurriculars
    6. Work-ex Plan

    Non-negotiable rule (§4):
    All benchmark descriptions and profile enhancement recommendations come directly
    from verified rows in kb.profile_audit_rubric and kb.profile_action.
    """
    def __init__(self, repo=None):
        self.repo = repo or core_to_mba_repo

    def _normalize_branch(self, branch: str) -> str:
        b = branch.upper().strip()
        if "EE" in b:
            return "EE"
        if "MM" in b or "META" in b:
            return "MM"
        return b

    def evaluate_profile(
        self,
        student_id: str,
        branch: str,
        cgpa: float,
        backlogs: int,
        projects: Optional[List[Dict[str, Any]]] = None,
        internships: Optional[List[Dict[str, Any]]] = None,
        leadership_roles: Optional[List[str]] = None,
        extracurriculars: Optional[List[str]] = None,
        work_ex_plan: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates 1-4 level scores for each criterion and recommends targeted actions.
        """
        projects = projects or []
        internships = internships or []
        leadership_roles = leadership_roles or []
        extracurriculars = extracurriculars or []
        norm_branch = self._normalize_branch(branch)

        scores: Dict[str, int] = {}
        explanations: Dict[str, str] = {}

        # 1. Academics
        if cgpa >= 8.5 and backlogs == 0:
            scores["Academics"] = 4
        elif cgpa >= 7.5 and backlogs == 0:
            scores["Academics"] = 3
        elif cgpa >= 6.5 and backlogs == 0:
            scores["Academics"] = 2
        else:
            scores["Academics"] = 1

        # 2. Projects
        # Look for flagship, business relevance, interdisciplinary, published
        has_flagship = any(
            p.get("is_flagship") or "competition" in p.get("title", "").lower() or "patent" in p.get("title", "").lower() or "paper" in p.get("title", "").lower()
            for p in projects
        )
        has_term_project = len(projects) >= 1
        if has_flagship:
            scores["Projects"] = 4
        elif len(projects) >= 2 or any(p.get("has_hardware") or p.get("is_sponsored") for p in projects):
            scores["Projects"] = 3
        elif has_term_project:
            scores["Projects"] = 2
        else:
            scores["Projects"] = 1

        # 3. Internships
        has_competitive_corp = any(
            i.get("is_corporate") or "client" in i.get("description", "").lower() or "savings" in i.get("description", "").lower()
            for i in internships
        )
        has_structured_8wk = any(i.get("duration_weeks", 0) >= 8 for i in internships) or len(internships) >= 1
        has_visit = any("visit" in i.get("title", "").lower() or "training" in i.get("title", "").lower() for i in internships)
        if has_competitive_corp:
            scores["Internships"] = 4
        elif has_structured_8wk:
            scores["Internships"] = 3
        elif has_visit or len(internships) > 0:
            scores["Internships"] = 2
        else:
            scores["Internships"] = 1

        # 4. Leadership / POR
        por_lower = " ".join(leadership_roles).lower()
        if any(w in por_lower for w in ["head", "convener", "president", "founder", "governor", "general secretary"]):
            scores["Leadership"] = 4
        elif any(w in por_lower for w in ["lead", "coordinator", "representative", "captain"]):
            scores["Leadership"] = 3
        elif any(w in por_lower for w in ["volunteer", "sub-coordinator", "member"]):
            scores["Leadership"] = 2
        else:
            scores["Leadership"] = 1

        # 5. Extracurriculars
        extra_lower = " ".join(extracurriculars).lower()
        if any(w in extra_lower for w in ["national", "state", "ngo founder", "social impact"]):
            scores["Extracurriculars"] = 4
        elif any(w in extra_lower for w in ["inter-college", "podium", "winner", "ngo", "rotaract"]):
            scores["Extracurriculars"] = 3
        elif len(extracurriculars) >= 1:
            scores["Extracurriculars"] = 2
        else:
            scores["Extracurriculars"] = 1

        # 6. Work-ex Plan
        w_lower = (work_ex_plan or "").lower()
        if any(w in w_lower for w in ["sponsor", "2-3 year", "strategic", "operations consulting"]):
            scores["Work-ex Plan"] = 4
        elif any(w in w_lower for w in ["core", "industry", "2 years", "operations", "tech"]):
            scores["Work-ex Plan"] = 3
        elif len(w_lower) > 10:
            scores["Work-ex Plan"] = 2
        else:
            scores["Work-ex Plan"] = 1

        # Retrieve rubric level texts
        criterion_details = {}
        for crit, lvl in scores.items():
            rub = self.repo.profile_audit_rubrics.get(crit)
            lvl_text = ""
            if rub:
                lvl_text = getattr(rub, f"level_{lvl}", "")
            criterion_details[crit] = {
                "level": lvl,
                "benchmark": lvl_text
            }

        total_score = sum(scores.values())
        if total_score >= 21:
            tier = "Top Tier (IIM Ahmedabad / Bangalore / Calcutta / ISB Profile)"
        elif total_score >= 16:
            tier = "Strong (IIM Lucknow / Kozhikode / Indore / XLRI Profile)"
        elif total_score >= 11:
            tier = "Competitive (New / Baby IIMs & Tier-2 B-Schools)"
        else:
            tier = "Emerging (Comprehensive Profile Enhancement Recommended)"

        # Engineering advantage
        eng_advantage = (
            f"As a {norm_branch} student with CGPA {cgpa:.2f}, your analytical problem-solving and structured technical "
            f"rigor provide high credibility for operations, supply chain, and product management roles. "
            f"In IIM and B-school shortlists, top engineering graduates stand out when their technical projects "
            f"are paired with clear business impact metrics."
        )

        # Select recommended actions for criteria with level < 3
        recommended_actions: List[Dict[str, Any]] = []
        for crit, lvl in scores.items():
            if lvl < 3:
                # Find matching actions in repo
                for act in self.repo.profile_actions.values():
                    if not act.reviewed:
                        continue
                    if act.criterion_improved == crit:
                        act_b = act.branch.upper()
                        if act_b in ["ANY", "ALL", norm_branch]:
                            recommended_actions.append({
                                "action_id": act.id,
                                "criterion": act.criterion_improved,
                                "action": act.action,
                                "effort_hours": act.effort_hours,
                                "timing": act.timing,
                                "course_code": act.course_code
                            })

        return {
            "student_id": student_id,
            "branch": norm_branch,
            "cgpa": cgpa,
            "backlogs": backlogs,
            "total_score": total_score,
            "max_score": 24,
            "tier": tier,
            "criteria_scores": criterion_details,
            "engineering_advantage": eng_advantage,
            "recommended_actions": recommended_actions
        }

# Global Singleton
mba_profile_audit_engine = MBAProfileAuditEngine()
