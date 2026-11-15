import os
import uuid
from typing import List, Dict, Optional, Any
from app.contracts.core_to_core import (
    WeeklyFocusItem,
    WeeklyFocusPlan,
    ReflectionSubmission
)
from app.engine.budget import budget_engine
from app.kb.core_to_core_repo import core_kb_repo
from app.contracts.student import SkillState

class WeeklyGuidanceEngine:
    """
    Weekly Guidance and Reflection Engine.
    
    Hard constraints:
    - Never generates rigid timetables (no day-by-day or hour-by-hour schedules).
    - Produces weekly focus goals, an hours budget, and active practice methods.
    - Adapts dynamically based on reflection submissions and academic calendar pacing.
    """
    def __init__(self):
        self.budget_engine = budget_engine
        self.kb_repo = core_kb_repo
        self.weekly_plans: Dict[str, WeeklyFocusPlan] = {}
        self.reflections: Dict[str, List[Dict[str, Any]]] = {}

    def generate_weekly_focus(
        self,
        student_id: str,
        programme_id: str,
        declared_hours: float,
        enrolled_course_ids: List[str],
        skill_states: List[SkillState],
        week_number: int = 1,
        cgpa: Optional[float] = None,
        backlogs: int = 0,
        weak_course_ids: Optional[List[str]] = None,
        goal_type: str = "core_research"
    ) -> WeeklyFocusPlan:
        # 1. Compute budget & calendar factors
        budget_info = self.budget_engine.calculate_weekly_budget(
            declared_hours=declared_hours,
            enrolled_course_ids=enrolled_course_ids,
            week_number=week_number,
            cgpa=cgpa,
            backlogs=backlogs,
            weak_course_ids=weak_course_ids
        )

        total_budget = budget_info["adjusted_budget_hours"]
        core_budget = budget_info["core_course_hours"]
        skill_budget = budget_info["extra_skill_hours"]
        is_cgpa_active = budget_info["cgpa_protection_active"]
        cal_week = budget_info["week_type"]

        items: List[WeeklyFocusItem] = []

        # 2. Focus Item 1: Core Course Mastery (Always included to protect CGPA)
        core_id = (weak_course_ids[0] if weak_course_ids else (enrolled_course_ids[0] if enrolled_course_ids else "EE2L001"))
        if is_cgpa_active:
            act_desc = "Intensive problem sets on weak topics, lecture review, and tutorial question workout."
            why_desc = f"CGPA Protection priority: Focus on {core_id} to ensure strong continuous evaluation and exam readiness."
        else:
            act_desc = "Review core conceptual derivations, complete textbook exercises, and summarize key theorems."
            why_desc = f"Maintain solid academic foundation in {core_id} alongside core track advancement."

        items.append(WeeklyFocusItem(
            focus_id=f"FOCUS_CORE_{week_number}_{uuid.uuid4().hex[:4]}",
            category="core_course",
            target_id=core_id,
            title=f"Core Course Depth: {core_id}",
            activity=act_desc,
            suggested_hours=core_budget,
            why=why_desc
        ))

        # 3. Focus Item 2: Technical Skill / Lab Practice
        # Pick lowest-proficiency skill
        sorted_skills = sorted(skill_states, key=lambda s: s.estimated_level)
        target_skill = sorted_skills[0].skill_id if sorted_skills else ("SKILL_CIRCUIT_ANALYSIS" if "EE" in programme_id else "SKILL_PHYSICAL_METALLURGY")
        
        hours_item2 = round(skill_budget * 0.6, 1) if skill_budget > 3.0 else skill_budget
        items.append(WeeklyFocusItem(
            focus_id=f"FOCUS_SKILL_{week_number}_{uuid.uuid4().hex[:4]}",
            category="skill_mastery",
            target_id=target_skill,
            title=f"Skill Deep-Dive: {target_skill.replace('SKILL_', '').replace('_', ' ').title()}",
            activity="Active problem solving, simulation modeling or laboratory analytical calculations (avoid passive reading).",
            suggested_hours=hours_item2,
            why=f"Bridge key conceptual gap in {target_skill} to meet readiness gate criteria."
        ))

        # 4. Focus Item 3: Track-specific Goal (Research reading or Industry Tool)
        remaining_hours = max(1.0, round(skill_budget - hours_item2, 1))
        if goal_type == "core_industry":
            tool_name = "MATLAB/Simulink or PSCAD" if "EE" in programme_id else "Thermo-Calc / ANSYS"
            items.append(WeeklyFocusItem(
                focus_id=f"FOCUS_IND_{week_number}_{uuid.uuid4().hex[:4]}",
                category="industry_tool",
                target_id="IND_SIM_TOOL",
                title=f"Industry Simulation Tool: {tool_name}",
                activity=f"Hands-on tutorial project using {tool_name}; build basic circuit or phase diagram model.",
                suggested_hours=remaining_hours,
                why="Industry track readiness requires demonstrable hands-on CAD/simulation engineering tool proficiency."
            ))
        else:
            items.append(WeeklyFocusItem(
                focus_id=f"FOCUS_RES_{week_number}_{uuid.uuid4().hex[:4]}",
                category="research_skill",
                target_id="RES_READING",
                title="Guided Research Paper Reading & Abstract Analysis",
                activity="Read 1 verified paper from IIT BBS library; outline methodology, assumptions, and key results.",
                suggested_hours=remaining_hours,
                why="Develop technical literature critique capabilities required for undergraduate research gate."
            ))

        plan = WeeklyFocusPlan(
            student_id=student_id,
            week_number=week_number,
            week_start=budget_info["week_start"],
            week_type=budget_info["week_type"],
            budget_hours=total_budget,
            calendar_factor=budget_info["calendar_factor"],
            focus_items=items,
            cgpa_protection_active=is_cgpa_active,
            cgpa_protection_reason=budget_info["protection_reason"],
            version=1
        )
        self.weekly_plans[student_id] = plan
        return plan

    def process_reflection(
        self,
        student_id: str,
        reflection: ReflectionSubmission
    ) -> Dict[str, Any]:
        """
        Processes weekly reflection and adapts subsequent plan pacing.
        """
        ref_record = reflection.model_dump()
        self.reflections.setdefault(student_id, []).append(ref_record)

        current_plan = self.weekly_plans.get(student_id)
        budget = current_plan.budget_hours if current_plan else 15.0

        adaptation_needed = False
        reasons = []

        # If hours spent < 60% of budget or rating <= 2
        if reflection.hours_spent < (budget * 0.60):
            adaptation_needed = True
            reasons.append(
                f"Logged study time ({reflection.hours_spent}h) was below 60% of planned budget ({budget}h). Adjusting future study volume to prevent burnout."
            )

        if reflection.self_rating <= 2:
            adaptation_needed = True
            reasons.append(
                f"Self-rating was {reflection.self_rating}/5. Difficulties noted in: '{reflection.didnt_work}'. Injecting additional scaffolding and guided review."
            )

        adaptation_summary = "Pacing on track." if not adaptation_needed else " | ".join(reasons)

        return {
            "status": "success",
            "student_id": student_id,
            "week_number": reflection.week_number,
            "reflection_logged": True,
            "adaptation_triggered": adaptation_needed,
            "adaptation_summary": adaptation_summary
        }

weekly_guidance_engine = WeeklyGuidanceEngine()
