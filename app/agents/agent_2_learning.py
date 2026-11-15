import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.contracts.plan import Plan, PlanItem
from app.contracts.student import StudentProfile, SkillState, Preference
from app.contracts.proposal import ChangeProposal
from app.contracts.kb import Resource
from app.kb.repositories import ResourceRepo, CourseRepo, SkillRepo

class LearningResourceAgent:
    """
    AGENT 2 — LEARNING / RESOURCE AGENT
    
    Responsibilities:
    1. Inspects student's current roadmap and active week.
    2. Recommends today's learning resources from the verified knowledge base (NPTEL, SWAYAM, MIT OCW).
    3. ZERO FABRICATION: Never invents URLs or fictitious titles.
    4. Provides alternatives when student flags difficulty using verified backup courseware.
    5. CANNOT MODIFY ROADMAP DIRECTLY: Emits structured ChangeProposals for student approval.
    """
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self.resource_repo = ResourceRepo(seed_dir)
        self.course_repo = CourseRepo(seed_dir)
        self.skill_repo = SkillRepo(seed_dir)

    def get_daily_recommendations(
        self,
        plan: Plan,
        current_week: int,
        student_skill_states: Dict[str, SkillState],
        preferences: Optional[List[Preference]] = None
    ) -> Dict[str, Any]:
        """
        Retrieves today's primary learning materials and practice exercises
        grounded in the active roadmap and knowledge-base resources.
        """
        # Extract active courses for the student's current semester
        active_courses = [it for it in plan.items if it.item_type == "course"]
        target_course_ids = [it.course_id for it in active_courses if it.course_id]

        recommended_resources: List[Dict[str, Any]] = []

        for cid in target_course_ids:
            course_obj = self.course_repo.get_by_id(cid)
            course_title = course_obj.title if course_obj else cid
            disp_code = course_obj.display_code if course_obj else cid

            # 1. Primary lookup via verified resource_course.csv mapping
            primary_res = self.resource_repo.get_primary_resource_for_course(cid)

            # 2. Fallback to title substring match only if not in resource_course
            if not primary_res:
                matches = [r for r in self.resource_repo.list_all() if cid in r.title or (course_obj and course_obj.course_code in r.title)]
                if matches:
                    primary_res = matches[0]

            if primary_res:
                recommended_resources.append({
                    "course_id": cid,
                    "display_code": disp_code,
                    "course_title": course_title,
                    "resource_id": primary_res.resource_id,
                    "title": primary_res.title,
                    "provider": primary_res.provider,
                    "url": primary_res.url,
                    "coverage_status": primary_res.coverage_status,
                    "difficulty": getattr(primary_res, "difficulty", "intermediate"),
                    "role": "primary_lecture"
                })

        return {
            "week_number": current_week,
            "total_recommended": len(recommended_resources),
            "resources": recommended_resources,
            "disclaimer": "All resource links are sourced directly from the verified institutional knowledge base."
        }

    def find_alternative_resource(
        self,
        current_resource_id: str,
        reason: str = "too_difficult"
    ) -> Dict[str, Any]:
        """
        Finds a beginner-friendly or alternative backup resource from the KB
        when a student encounters difficulty with the primary resource.
        Returns explicit 'not found' response if no alternative exists (never fabricates URLs).
        """
        alt = self.resource_repo.get_alternative_resource(current_resource_id)
        if alt:
            return {
                "found": True,
                "resource_id": alt.resource_id,
                "title": alt.title,
                "provider": alt.provider,
                "url": alt.url,
                "difficulty": getattr(alt, "difficulty", "introductory"),
                "coverage_status": alt.coverage_status,
                "note": f"Alternative recommended because primary resource was reported as {reason}."
            }

        return {
            "found": False,
            "resource_id": None,
            "title": None,
            "url": None,
            "message": "No suitable resource found in the current knowledge base"
        }

    def propose_resource_swap(
        self,
        student_id: str,
        current_resource_id: str,
        replacement_resource: Dict[str, Any],
        target_week: int,
        reason: str
    ) -> ChangeProposal:
        """
        Creates a structured ChangeProposal proposing a resource change.
        Strict rule: Does NOT write to the roadmap.
        """
        return ChangeProposal(
            proposal_id=f"PROP_RES_{uuid.uuid4().hex[:8]}",
            student_id=student_id,
            proposer_agent="agent_2_resource",
            proposal_type="resource_swap",
            status="pending_student_approval",
            reasoning=f"Resource update: {reason}",
            target_week=target_week,
            proposed_modifications={
                "current_resource_id": current_resource_id,
                "replacement_resource_id": replacement_resource.get("resource_id"),
                "replacement_title": replacement_resource.get("title"),
                "replacement_url": replacement_resource.get("url")
            },
            impact_summary=f"Replaces current module with '{replacement_resource.get('title')}' for clearer foundation.",
            created_at=datetime.now(timezone.utc)
        )
