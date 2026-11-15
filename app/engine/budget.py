import os
from typing import List, Dict, Optional, Any, Tuple
from app.kb.core_to_core_repo import core_kb_repo
from app.kb.repositories import CourseRepo
from app.contracts.core_to_core import AcademicCalendarWeek

class BudgetEngine:
    """
    Deterministic Free-Hours Budget and Academic Calendar Engine.
    
    Hard constraints:
    - Never generates rigid timetables (no day-by-day or hour-by-hour schedules).
    - Outputs weekly hours budget, suggested activities, and study approaches.
    - Enforces CGPA protection: core-course support prioritized over extra research/skills
      when course proficiency is low or during midsem/endsem exam weeks.
    """
    def __init__(self, course_repo: Optional[CourseRepo] = None):
        self.course_repo = course_repo or CourseRepo()
        self.kb_repo = core_kb_repo

    def parse_ltp_contact_hours(self, ltp_str: Optional[str]) -> float:
        """
        Parses L-T-P format (e.g. '3-1-0' -> 4.0 hours, '3-0-3' -> 6.0 hours).
        Defaults to 3.0 contact hours if unspecified.
        """
        if not ltp_str or not isinstance(ltp_str, str):
            return 3.0
        parts = ltp_str.strip().split("-")
        try:
            if len(parts) >= 3:
                return float(parts[0]) + float(parts[1]) + float(parts[2])
            elif len(parts) == 1:
                return float(parts[0])
        except Exception:
            pass
        return 3.0

    def compute_contact_hours(self, enrolled_course_ids: List[str]) -> float:
        """
        Calculates total weekly in-class contact hours: sum(L + T + P).
        """
        total = 0.0
        for cid in enrolled_course_ids:
            course = self.course_repo.get_by_id(cid)
            if course:
                total += self.parse_ltp_contact_hours(course.ltp)
            else:
                total += 3.0 # Fallback 3 hrs per course
        return total

    def get_calendar_week(self, week_number: int = 1) -> AcademicCalendarWeek:
        """
        Retrieves the academic calendar week metadata.
        """
        week = self.kb_repo.get_calendar_week(week_number)
        if not week:
            # Fallback default week 1 teaching
            return AcademicCalendarWeek(
                semester="Autumn 2026",
                week_number=week_number,
                week_start="2026-08-03",
                week_type="teaching",
                calendar_factor=1.0,
                source_url="https://www.iitbbs.ac.in/academic-calendar",
                verified=True
            )
        return week

    def calculate_weekly_budget(
        self,
        declared_hours: float,
        enrolled_course_ids: List[str],
        week_number: int = 1,
        cgpa: Optional[float] = None,
        backlogs: int = 0,
        weak_course_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Computes weekly study budget and CGPA protection distribution.
        """
        contact_hours = self.compute_contact_hours(enrolled_course_ids)
        cal_week = self.get_calendar_week(week_number)
        factor = cal_week.calendar_factor

        # Standard academic weekly ceiling = 50.0 hours total
        max_extra_hours = max(5.0, 50.0 - contact_hours)
        base_budget = min(declared_hours, max_extra_hours)
        adjusted_budget = round(base_budget * factor, 1)

        # CGPA Protection Rule
        # Triggers if:
        # 1. CGPA < 7.5 or backlogs > 0
        # 2. Identified weak current courses
        # 3. Exam week (midsem / endsem)
        is_exam_week = cal_week.week_type in ["midsem", "endsem"]
        has_academic_risk = (cgpa is not None and cgpa < 7.5) or backlogs > 0 or bool(weak_course_ids)

        cgpa_protection_active = is_exam_week or has_academic_risk
        reason = None

        if cgpa_protection_active:
            if is_exam_week:
                core_pct = 0.80 if cal_week.week_type == "endsem" else 0.70
                reason = (
                    f"CGPA protection: During {cal_week.week_type} week (factor {factor}), "
                    f"{int(core_pct*100)}% of your free-hours budget is reserved for core-course revision."
                )
            else:
                core_pct = 0.65
                reason = (
                    "CGPA protection: Core-course support prioritized over external research/skills "
                    "to safeguard academic standing and semester grade trajectory."
                )
            core_course_hours = round(adjusted_budget * core_pct, 1)
            extra_skill_hours = round(adjusted_budget - core_course_hours, 1)
        else:
            core_pct = 0.35
            core_course_hours = round(adjusted_budget * core_pct, 1)
            extra_skill_hours = round(adjusted_budget - core_course_hours, 1)
            reason = "Standard academic balance: Routine core course review with active skill exploration."

        return {
            "week_number": week_number,
            "week_start": cal_week.week_start,
            "week_type": cal_week.week_type,
            "calendar_factor": factor,
            "contact_hours": contact_hours,
            "declared_hours": declared_hours,
            "adjusted_budget_hours": adjusted_budget,
            "core_course_hours": core_course_hours,
            "extra_skill_hours": extra_skill_hours,
            "cgpa_protection_active": cgpa_protection_active,
            "protection_reason": reason
        }

budget_engine = BudgetEngine()
