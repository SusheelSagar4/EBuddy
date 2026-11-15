import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime
from app.contracts.core_to_mtech import (
    PrepTemplate,
    TemplatePhase,
    SyllabusTopic,
    TopicWeightage,
    CourseTopicMap
)
from app.kb.core_to_mtech_repo import core_to_mtech_repo
from app.engine.budget import BudgetEngine

class GATEPlannerEngine:
    """
    Deterministic GATE Topic Priority & Weekly Guidance Engine (§8.3).
    Hard constraints:
    - Zero rigid timetables: NEVER outputs day-by-day or hour-by-hour schedules.
    - Priority = average weightage over stored years × (1 − mastery) × prerequisite factor.
    - Double benefit tagging for topics covered in current semester courses.
    - CGPA protection: Core course share comes first in exam weeks or for students with weak CGPA/backlogs.
    - Adapts prep templates to weeks remaining; if too few weeks, offers faster template + reduced priority scope.
    """
    def __init__(self, repo=None, budget_engine=None):
        self.repo = repo or core_to_mtech_repo
        self.budget_engine = budget_engine or BudgetEngine()

    def compute_weeks_remaining(self, target_cycle: str = "2027", current_date: Optional[date] = None) -> int:
        cur_d = current_date or date(2026, 11, 15)
        # Find cycle in repo
        cycle_obj = next((c for c in self.repo.exam_cycles.values() if c.cycle == target_cycle), None)
        if cycle_obj and cycle_obj.exam_dates:
            # First exam date in string (e.g., "2027-02-06")
            try:
                first_date_str = cycle_obj.exam_dates.split(",")[0].strip()
                exam_d = datetime.strptime(first_date_str, "%Y-%m-%d").date()
                delta_days = (exam_d - cur_d).days
                return max(1, delta_days // 7)
            except Exception:
                pass
        return 12 # Default ~12 weeks

    def select_template_and_phases(
        self,
        paper_code: str,
        weeks_remaining: int,
        preferred_speed_months: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Selects template and stretches/compresses phase durations to match weeks remaining.
        If preferred template requires more weeks than available, flags warning and offers faster template (§8.3).
        """
        p_code = paper_code.upper()
        speed = preferred_speed_months or (12 if weeks_remaining >= 24 else (6 if weeks_remaining >= 12 else 3))
        
        weeks_too_few = False
        warning_msg = None
        best_valid_option = None

        if speed == 12 and weeks_remaining < 24:
            weeks_too_few = True
            speed = 3 if weeks_remaining <= 12 else 6
            warning_msg = (
                f"Notice: {weeks_remaining} weeks remaining to GATE {p_code} is insufficient for a 12-month comprehensive template. "
                f"Switching to {speed}-Month Fast Track template with high-yield topic scope."
            )
            best_valid_option = f"Adopt {speed}-Month High-Yield template prioritizing top 65% weightage core syllabus."
        elif speed == 6 and weeks_remaining < 8:
            weeks_too_few = True
            speed = 3
            warning_msg = (
                f"Notice: {weeks_remaining} weeks remaining to GATE {p_code} is insufficient for a 6-month template. "
                "Switching to 3-Month Intensive Mock & Revision template."
            )
            best_valid_option = "Adopt 3-Month Intensive template focusing on PYQs and high-frequency topics."

        template_id = f"SAMPLE-TMPL-{p_code}-{speed}M"
        tmpl = self.repo.prep_templates.get(template_id)
        if not tmpl:
            # Fallback to available
            template_id = f"SAMPLE-TMPL-{p_code}-3M"
            tmpl = self.repo.prep_templates.get(template_id)

        raw_phases = self.repo.get_phases_for_template(template_id)
        adjusted_phases = []
        allocated_weeks = 0

        for idx, p in enumerate(raw_phases):
            # Proportional weeks based on share_of_weeks
            if idx == len(raw_phases) - 1:
                p_weeks = max(1, weeks_remaining - allocated_weeks)
            else:
                p_weeks = max(1, round(p.share_of_weeks * weeks_remaining))
                allocated_weeks += p_weeks

            adjusted_phases.append({
                "phase_order": p.phase_order,
                "name": p.name,
                "share_of_weeks": p.share_of_weeks,
                "duration_weeks": p_weeks,
                "topic_selector": p.topic_selector,
                "checkpoint": p.checkpoint,
                "activities": p.activities
            })

        return {
            "template_id": template_id,
            "speed_months": speed,
            "weeks_remaining": weeks_remaining,
            "weeks_too_few": weeks_too_few,
            "warning": warning_msg,
            "best_valid_option": best_valid_option,
            "phases": adjusted_phases
        }

    def compute_topic_priorities(
        self,
        paper_code: str,
        topic_masteries: Dict[str, float],
        current_course_codes: List[str]
    ) -> List[Dict[str, Any]]:
        """
        priority(topic) = average weightage over stored years × (1 − mastery) × prerequisite factor.
        """
        topics = self.repo.get_topics_for_paper(paper_code)
        course_map = self.repo.get_course_mapped_topics(current_course_codes)
        priorities = []

        for t in topics:
            avg_wt = self.repo.get_average_weightage(t.id)
            mastery = topic_masteries.get(t.id, 0.0)
            gap = max(0.05, 1.0 - mastery)

            # Prerequisite factor: higher for foundational Math, Circuits, Thermo
            is_foundational = t.section in ["Engineering Mathematics", "General Aptitude"] or t.id in [
                "SAMPLE-TOPIC-EE-CIRCUITS", "SAMPLE-TOPIC-MT-THERMO"
            ]
            prereq_factor = 1.25 if is_foundational else 1.0

            score = round(avg_wt * gap * prereq_factor, 2)
            has_double_benefit = t.id in course_map

            priorities.append({
                "topic_id": t.id,
                "topic_name": t.topic,
                "section": t.section,
                "average_weightage": avg_wt,
                "mastery": mastery,
                "gap": round(gap, 2),
                "prerequisite_factor": prereq_factor,
                "priority_score": score,
                "double_benefit": has_double_benefit,
                "mapped_course": course_map.get(t.id)
            })

        # Sort descending by priority score
        priorities.sort(key=lambda x: x["priority_score"], reverse=True)
        return priorities

    def generate_weekly_guidance(
        self,
        student_id: str,
        week_num: int,
        paper_code: str,
        cgpa: float,
        backlogs: int,
        hours_available: float,
        current_course_codes: List[str],
        topic_masteries: Dict[str, float],
        weeks_remaining: int,
        top_error_tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generates weekly guidance strictly following PS rules (§4 & §8.3):
        - Never a rigid timetable (no day-by-day schedule).
        - CGPA protection prioritized first for weak students or during exam weeks.
        - 2-4 weekly focus cards with: what, how, why, resource ID, hours.
        """
        cal_week = self.budget_engine.get_calendar_week(week_num)
        cal_factor = cal_week.calendar_factor # 1.0 teaching, 0.4-0.5 exams

        # CGPA Protection Policy (§4)
        is_exam_week = cal_week.week_type.lower() in ["midsem", "endsem", "exam"]
        is_at_risk = cgpa < 7.0 or backlogs > 0

        cgpa_protection_active = False
        trade_off_explanation = None

        if is_exam_week:
            cgpa_share = 0.70
            gate_share = 0.30
            cgpa_protection_active = True
            trade_off_explanation = (
                f"CGPA Protection Activated: Week {week_num} is {cal_week.week_type}. "
                "70% of available study budget is protected for institute course exams to safeguard your degree CGPA."
            )
        elif is_at_risk:
            cgpa_share = 0.55
            gate_share = 0.45
            cgpa_protection_active = True
            trade_off_explanation = (
                f"CGPA Protection Activated: Current CGPA ({cgpa:.2f}) or active backlogs ({backlogs}) require academic safeguarding. "
                "Core-course support prioritized before extra GATE preparation."
            )
        else:
            cgpa_share = 0.30
            gate_share = 0.70

        total_effective_hours = hours_available * cal_factor
        gate_hours_total = round(total_effective_hours * gate_share, 1)
        cgpa_hours_total = round(total_effective_hours * cgpa_share, 1)

        # Topic priorities
        priorities = self.compute_topic_priorities(paper_code, topic_masteries, current_course_codes)

        # Select 2 to 3 priority topics + error remediation if present
        focus_items = []
        selected_topics = priorities[:3]

        # Allocate hours across selected items
        item_hour_budget = round(gate_hours_total / max(1, len(selected_topics)), 1)

        for top in selected_topics:
            tid = top["topic_id"]
            double_tag = f" [Double Benefit: Covers current syllabus {top['mapped_course']}]" if top["double_benefit"] else ""
            
            # Suggest appropriate active practice method
            if top["mastery"] < 0.30:
                method = "Active recall on core formulas, followed by 10 standard practice exercises"
            elif top["mastery"] < 0.65:
                method = "Past 5-year GATE PYQs by topic under timed sectional conditions"
            else:
                method = "Advanced numerical questions (NAT) and error-log mistake analysis"

            focus_items.append({
                "item_id": f"FOCUS-{tid}",
                "topic_id": tid,
                "topic_name": top["topic_name"] + double_tag,
                "section": top["section"],
                "what": f"Targeted problem-solving and concept consolidation on {top['topic_name']}.",
                "how": method,
                "why": f"Topic accounts for ~{top['average_weightage']} marks (past 5-yr avg). Current tested mastery is {int(top['mastery']*100)}%.",
                "resource_id": f"RES-GATE-{top['section'].upper()[:4]}",
                "suggested_hours": item_hour_budget,
                "double_benefit": top["double_benefit"],
                "status": "pending"
            })

        # Add mock slot if in final revision or mock phase (weeks_remaining <= 6)
        if weeks_remaining <= 6 and gate_hours_total >= 4.0:
            focus_items.append({
                "item_id": "FOCUS-MOCK-ANALYSIS",
                "topic_id": "ALL_SYLLABUS",
                "topic_name": "Full-Length 3-Hour Mock & Error-Log Review",
                "section": "Timed Simulation",
                "what": "Complete one full-length 65-question timed mock exam under standard GATE interface conditions.",
                "how": "3 hours timed test + 1.5 hours error log audit categorizing mistakes (concept vs calculation vs time).",
                "why": "Builds time management, negative-marking discipline, and calibrates realistic score band.",
                "resource_id": "RES-GATE-FULL-MOCK",
                "suggested_hours": 4.5,
                "double_benefit": False,
                "status": "pending"
            })

        return {
            "student_id": student_id,
            "week_number": week_num,
            "week_type": cal_week.week_type,
            "calendar_factor": cal_factor,
            "hours_budget": {
                "total_available_outside_class": hours_available,
                "calendar_adjusted_total": total_effective_hours,
                "cgpa_protection_hours": cgpa_hours_total,
                "gate_prep_hours": gate_hours_total
            },
            "cgpa_protection_active": cgpa_protection_active,
            "trade_off_explanation": trade_off_explanation,
            "weekly_focus_items": focus_items,
            "timetable_policy": "FLEXIBLE_GOALS_ONLY",
            "timetable_notice": "No rigid timetable is generated. You decide when to complete your weekly hours budget."
        }

# Global singleton
gate_planner_engine = GATEPlannerEngine()
