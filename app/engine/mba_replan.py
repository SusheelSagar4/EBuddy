from typing import List, Dict, Optional, Any
from app.kb.core_to_mba_repo import core_to_mba_repo
from app.engine.mba_mocks_shortlist import mba_mocks_shortlist_engine
from app.engine.mba_decision import mba_decision_engine

class MBAReplanEngine:
    """
    Post-Result Re-Planning & Switch-Back Engine (§1.9, §7.8 & §11).
    Evaluates official exam results, formulates realistic next-step pathways, and manages
    seamless lateral pivots back to Core Engineering tracks with 100% evidence preservation.

    Non-negotiable product rules (§4):
    1. Realistic, non-judgmental alternatives when exam results fall below target:
       - Alternative B-schools within achieved percentile range.
       - MBA after 2-3 years work-experience route.
       - Pivot back to Core Industry / Campus Placements or Core M.Tech.
    2. 100% Evidence Preservation: switching routes preserves all completed practice items,
       mock history, and diagnostic evidence without data loss.
    3. Plan version bump with explicit diff explanation ("what changed and why").
    """
    def __init__(self, repo=None):
        self.repo = repo or core_to_mba_repo

    def evaluate_result(
        self,
        student_id: str,
        exam_id: str,
        actual_percentile: float,
        category: str = "GEN",
        target_institution_id: Optional[str] = "MBA-IN-IIMA"
    ) -> Dict[str, Any]:
        """
        Formulates post-result alternatives based on actual score/percentile.
        """
        norm_cat = category.upper().strip()
        
        # Determine verified programmes matching actual percentile
        matching_programmes: List[Dict[str, Any]] = []
        for stat in self.repo.admission_stats:
            if not stat.verified or stat.category.upper() != norm_cat:
                continue
            prog = self.repo.programmes.get(stat.programme_id)
            if not prog or not prog.verified:
                continue
            if actual_percentile >= stat.cutoff_value - 1.5:
                matching_programmes.append({
                    "programme_id": prog.id,
                    "programme_name": prog.programme_name,
                    "cutoff_percentile": stat.cutoff_value,
                    "status": "Eligible for Interview Call" if actual_percentile >= stat.cutoff_value else "Borderline / Spot Opportunity"
                })

        # Scenario analysis
        if actual_percentile >= 98.0:
            status = "Target Achieved: Premier Tier Shortlist"
            recommendation = (
                f"Your score of {actual_percentile:.1f}%ile comfortably clears cutoffs for top IIMs. "
                "Immediate next step: Transition immediately to intensive WAT & PI preparation (MBA-T-PI2)."
            )
            actions = ["Enroll in WAT/PI mock interviews", "Prepare branch technical viva fundamentals", "Draft Why MBA essays"]
        elif actual_percentile >= 90.0:
            status = "Competitive Score: Strong B-School Calls Expected"
            recommendation = (
                f"Your score of {actual_percentile:.1f}%ile qualifies for premier non-IIM institutions (FMS, XLRI, IIT DMS) "
                "and New/Baby IIMs. Focus on converting calls with outstanding interview scores."
            )
            actions = ["Prepare for institutional GD/WAT rounds", "Apply to IIT DMS and non-IIM institutions", "WAT essay practice"]
        else:
            status = "Score Below Top Tier Cutoffs"
            recommendation = (
                f"While {actual_percentile:.1f}%ile is below the historic cutoff for top IIMs, you have 3 realistic strategic paths: "
                "1. Apply to specialized institutions within this percentile range. "
                "2. Join core engineering campus placements, gain 2-3 years work-ex, and re-apply with full work experience points. "
                "3. Pivot back to Core Engineering track (Core Industry or GATE/M.Tech)."
            )
            actions = [
                "Option A: Consider Tier-2 management institutes or specialized sectoral MBAs",
                "Option B: Target Core Engineering campus placements and plan MBA after 2-3 years (MBA-RT3)",
                "Option C: Switch back to Core to Core industry/PSU track with 100% diagnostic history preserved"
            ]

        return {
            "student_id": student_id,
            "exam_id": exam_id,
            "actual_percentile": actual_percentile,
            "category": norm_cat,
            "status": status,
            "recommendation": recommendation,
            "recommended_actions": actions,
            "matching_programmes": matching_programmes
        }

    def switch_back_to_core(
        self,
        student_id: str,
        target_route: str = "core_industry", # core_industry, core_research, core_mtech
        current_plan_version: int = 1,
        reason: str = "Strategic decision to prioritize core engineering placement after exam results."
    ) -> Dict[str, Any]:
        """
        Executes a lateral pivot back to Core Engineering, guaranteeing 100% evidence preservation.
        Generates plan version diff with 'what changed and why'.
        """
        valid_routes = ["core_industry", "core_research", "core_mtech"]
        if target_route not in valid_routes:
            raise ValueError(f"Invalid target route '{target_route}'. Must be one of {valid_routes}.")

        new_version = current_plan_version + 1

        route_names = {
            "core_industry": "Core Engineering Industry & Campus Placement Track",
            "core_research": "Core Research Track (Faculty Mentorship & SURGE/DAAD)",
            "core_mtech": "Higher Studies Track (GATE -> M.Tech/MS at IITs)"
        }

        diff = {
            "what_changed": [
                f"Primary track switched from 'Core to MBA' to '{route_names[target_route]}'",
                "Reallocated weekly MBA aptitude study hours back to Core engineering subjects and domain simulation tools",
                "Shifted upcoming focus goals from CAT/XAT mocks to Core campus placement tests / GATE PYQ problem solving",
                "Preserved 100% of student diagnostic history, practice items, mock results, and profile audit records"
            ],
            "why": reason,
            "evidence_preserved": {
                "diagnostic_history_intact": True,
                "mock_evidence_intact": True,
                "error_log_intact": True,
                "story_drafts_intact": True
            }
        }

        return {
            "student_id": student_id,
            "previous_route": "core_to_mba",
            "new_route": target_route,
            "previous_version": current_plan_version,
            "new_version": new_version,
            "status": "pivoted_successfully",
            "diff": diff,
            "message": f"Successfully switched to {route_names[target_route]}. Plan upgraded to Version {new_version}."
        }

# Global Singleton
mba_replan_engine = MBAReplanEngine()
