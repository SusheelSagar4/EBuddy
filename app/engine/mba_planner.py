import os
import math
from typing import List, Dict, Optional, Any
from app.contracts.core_to_mba import MBAPrepTemplate, MBATemplatePhase, ProfileAction
from app.kb.core_to_mba_repo import core_to_mba_repo
from app.engine.validator import PlanValidator

class MBAPlannerEngine:
    """
    Weekly Guidance and Pacing Engine (§1.4, §7.4 & §11).
    Generates semester-aware, weekly-budgeted preparation plans for Core to MBA students.

    Non-negotiable product rules (§4):
    1. NEVER a rigid timetable: outputs weekly focus goals and hours budgets only.
    2. CGPA Protection First: during mid-sems (weeks 7-8), end-sems (weeks 14-16), or for students
       with active backlogs / CGPA < 7.5, semester course work takes strict priority.
    3. Verbal-Gap Remediation: allocates extra reading volume (MBA-L1) and RC practice for students
       weak in VARC, while using Quant as a confidence-builder rather than over-practising.
    4. Profile Actions: max 1 action/week on non-exam weeks, validating course codes via PlanValidator.
    """
    def __init__(self, repo=None, validator=None):
        self.repo = repo or core_to_mba_repo
        self.validator = validator or PlanValidator()

    def generate_plan(
        self,
        student_id: str,
        branch: str,
        current_cgpa: float,
        backlogs: int,
        free_hours_per_week: float = 14.0,
        total_weeks: int = 16,
        target_exam_id: str = "MBA-EX-CAT",
        verbal_gap: bool = False,
        profile_actions: Optional[List[str]] = None,
        completed_course_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generates a 16-week adaptive preparation plan adhering to CGPA protection and pacing rules.
        """
        norm_branch = "EE" if "EE" in branch.upper() else ("MM" if "MM" in branch.upper() else branch)
        
        # 1. Select template based on total_weeks
        if total_weeks >= 40:
            template_id = "MBA-T-CAT12"
        elif total_weeks >= 20:
            template_id = "MBA-T-CAT6"
        else:
            template_id = "MBA-T-CAT3"

        template = self.repo.prep_templates.get(template_id)
        phases = self.repo.template_phases.get(template_id, [])
        if not phases:
            # Fallback to standard 4 phases
            phases = [
                MBATemplatePhase(template_id=template_id, order=1, name="Foundations & Verbal Habit", share_of_weeks=0.25, sections="QA;VARC;DILR", checkpoint="Foundational drills >= 60%"),
                MBATemplatePhase(template_id=template_id, order=2, name="Building & Sectional Tests", share_of_weeks=0.25, sections="QA;VARC;DILR", checkpoint="Sectionals >= 60%"),
                MBATemplatePhase(template_id=template_id, order=3, name="Full Mocks & Calibration", share_of_weeks=0.35, sections="QA;VARC;DILR", checkpoint="At least 2 full mocks"),
                MBATemplatePhase(template_id=template_id, order=4, name="Exam Stamina & Strategy", share_of_weeks=0.15, sections="QA;VARC;DILR", checkpoint="Final calibrated band")
            ]

        # Verify shares strictly sum to 1.0 (with float tolerance)
        total_share = sum(p.share_of_weeks for p in phases)
        if abs(total_share - 1.0) > 0.01:
            raise ValueError(f"Template phase shares sum to {total_share}, must sum to 1.0.")

        # Assign week ranges to each phase
        phase_allocations = []
        cur_w = 1
        for p in phases:
            w_count = max(1, round(p.share_of_weeks * total_weeks))
            start_w = cur_w
            end_w = min(total_weeks, cur_w + w_count - 1)
            phase_allocations.append({
                "phase": p,
                "start_week": start_w,
                "end_week": end_w
            })
            cur_w = end_w + 1
        # Adjust last phase to end exactly at total_weeks
        if phase_allocations:
            phase_allocations[-1]["end_week"] = total_weeks

        # Identify profile actions to schedule
        actions_to_schedule = []
        for act in self.repo.profile_actions.values():
            if not act.reviewed:
                continue
            act_b = act.branch.upper()
            if act_b in ["ANY", "ALL", norm_branch]:
                # If course code present, validate course existence
                if act.course_code:
                    if act.course_code not in self.validator.valid_courses:
                        continue
                actions_to_schedule.append(act)

        # Distribute at most 1 action per non-exam week
        action_idx = 0
        exam_weeks = {7, 8, 14, 15, 16}

        weeks: List[Dict[str, Any]] = []
        for w in range(1, total_weeks + 1):
            is_midsem = (w in [7, 8])
            is_endsem = (w in [14, 15, 16])
            is_exam = is_midsem or is_endsem

            # Determine active phase
            active_phase_name = "Preparation Phase"
            active_checkpoint = ""
            for pa in phase_allocations:
                if pa["start_week"] <= w <= pa["end_week"]:
                    active_phase_name = pa["phase"].name
                    active_checkpoint = pa["phase"].checkpoint or ""
                    break

            # Hours allocation (CGPA first rule)
            if is_exam:
                core_hours = min(free_hours_per_week, 12.0)
                mba_hours = max(0.0, min(2.0, free_hours_per_week - core_hours))
                qa_h = 0.0
                dilr_h = 0.0
                varc_h = mba_hours  # Only light reading to keep habit alive
                mock_h = 0.0
                alert = (
                    "Mid-Semester Exams Week: All intensive MBA prep throttled. Prioritize semester GPA."
                    if is_midsem else
                    "End-Semester Exams Week: Zero mock tests. Focus 100% on academic grade clearance."
                )
                scheduled_action = None
            else:
                # Normal or backlog protection
                if backlogs > 0 or current_cgpa < 7.2:
                    core_hours = min(free_hours_per_week * 0.55, 8.0)
                else:
                    core_hours = 4.0  # Routine semester maintenance
                
                mba_hours = max(2.0, free_hours_per_week - core_hours)
                
                # Section split
                if verbal_gap:
                    varc_h = round(mba_hours * 0.45, 1)
                    dilr_h = round(mba_hours * 0.30, 1)
                    qa_h = round(mba_hours * 0.25, 1)
                else:
                    varc_h = round(mba_hours * 0.30, 1)
                    dilr_h = round(mba_hours * 0.35, 1)
                    qa_h = round(mba_hours * 0.35, 1)

                mock_h = 2.0 if "mock" in active_phase_name.lower() or w >= 10 else 0.0
                alert = None

                # Schedule profile action if available (max 1 per week, non-exam)
                scheduled_action = None
                if action_idx < len(actions_to_schedule) and (w % 2 == 1):
                    scheduled_action = {
                        "action_id": actions_to_schedule[action_idx].id,
                        "action": actions_to_schedule[action_idx].action,
                        "criterion": actions_to_schedule[action_idx].criterion_improved,
                        "effort_hours": actions_to_schedule[action_idx].effort_hours,
                        "course_code": actions_to_schedule[action_idx].course_code
                    }
                    action_idx += 1

            # Focus goals
            focus_goals = []
            if is_exam:
                focus_goals.append("Semester course revision and previous-year university paper solutions")
                if mba_hours > 0:
                    focus_goals.append("Maintain 30 mins bedtime reading of long-form articles (MBA-L1)")
            else:
                if verbal_gap:
                    focus_goals.append(f"Verbal focus: 45 mins daily editorial reading + 4 RC passages ({varc_h} hrs total)")
                else:
                    focus_goals.append(f"VARC practice: 3 RC passages and critical reasoning drills ({varc_h} hrs total)")
                focus_goals.append(f"DILR practice: 4 reasoning arrangements / data matrix sets ({dilr_h} hrs total)")
                focus_goals.append(f"QA focus: Concept application & error log review ({qa_h} hrs total)")
                if mock_h > 0:
                    focus_goals.append("Full-length CAT simulation + 2-hour systematic error analysis (MBA-L2)")
                if scheduled_action:
                    focus_goals.append(f"Profile Action: {scheduled_action['action']} ({scheduled_action['criterion']})")

            # Learning methods
            methods = ["MBA-L8 (Semester-aware load)"]
            if is_exam:
                methods.append("MBA-L1 (Daily reading)")
            else:
                methods.extend(["MBA-L1 (Daily reading)", "MBA-L3 (Error log)"])
                if mock_h > 0:
                    methods.append("MBA-L2 (Mock analysis)")
                    methods.append("MBA-L4 (Selective attempting)")

            weeks.append({
                "week_number": w,
                "phase_name": active_phase_name,
                "checkpoint": active_checkpoint,
                "is_exam_week": is_exam,
                "alert": alert,
                "hours_budget": {
                    "total_available": free_hours_per_week,
                    "core_courses": round(core_hours, 1),
                    "mba_total": round(mba_hours, 1),
                    "qa": qa_h,
                    "dilr": dilr_h,
                    "varc": varc_h,
                    "mocks": mock_h
                },
                "focus_goals": focus_goals,
                "profile_action": scheduled_action,
                "recommended_methods": methods
            })

        return {
            "student_id": student_id,
            "branch": norm_branch,
            "cgpa": current_cgpa,
            "backlogs": backlogs,
            "total_weeks": total_weeks,
            "template_id": template_id,
            "cgpa_protection_active": (backlogs > 0 or current_cgpa < 7.5),
            "verbal_gap_protocol": verbal_gap,
            "weekly_schedule": weeks
        }

# Global Singleton
mba_planner_engine = MBAPlannerEngine()
