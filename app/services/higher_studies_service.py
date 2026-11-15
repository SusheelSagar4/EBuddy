import os
from typing import List, Dict, Any, Optional
from app.contracts.student import StudentProfile
from app.engine.gate_readiness_shortlist import GATEReadinessAndShortlistEngine
from app.engine.mba_mocks_shortlist import MBAMocksShortlistEngine
from app.engine.field_planner import field_planner_engine
from app.contracts.roadmap import WeeklyRoadmap

def calculate_cgpa_maintenance(
    current_cgpa: float,
    current_semester: int,
    target_cgpa: float = 8.0,
    total_semesters: int = 8
) -> Dict[str, Any]:
    """
    Requirement F9 CGPA Maintenance Formula:
    Calculates the exact SGPA needed in remaining semesters to achieve target CGPA.
    
    Formula:
      completed_sems = max(1, current_semester - 1)
      remaining_sems = max(1, total_semesters - completed_sems)
      current_points = current_cgpa * completed_sems
      target_points = target_cgpa * total_semesters
      required_sgpa = (target_points - current_points) / remaining_sems
    """
    completed_sems = max(1, current_semester - 1)
    remaining_sems = max(1, total_semesters - completed_sems)
    current_points = current_cgpa * completed_sems
    target_points = target_cgpa * total_semesters
    needed_points = target_points - current_points
    required_sgpa = needed_points / remaining_sems
    
    max_achievable = (current_points + 10.0 * remaining_sems) / total_semesters
    is_achievable = required_sgpa <= 10.0
    is_already_achieved = required_sgpa <= current_cgpa

    if required_sgpa > 10.0:
        advice = (
            f"Mathematically impossible: Target CGPA of {target_cgpa:.2f} requires an average SGPA of {required_sgpa:.2f} "
            f"across remaining {remaining_sems} semesters (maximum possible SGPA is 10.0). "
            f"Maximum achievable CGPA is {max_achievable:.2f}."
        )
    elif is_already_achieved:
        advice = (
            f"Target CGPA of {target_cgpa:.2f} is well within reach! You need an average SGPA of {max(0.0, required_sgpa):.2f} "
            f"over the next {remaining_sems} semesters to maintain your target."
        )
    else:
        advice = (
            f"To reach target CGPA of {target_cgpa:.2f} by graduation, you need to score an average SGPA of "
            f"at least {required_sgpa:.2f} in each of the remaining {remaining_sems} semesters."
        )

    return {
        "current_cgpa": round(current_cgpa, 2),
        "target_cgpa": round(target_cgpa, 2),
        "completed_semesters": completed_sems,
        "remaining_semesters": remaining_sems,
        "required_average_sgpa": round(required_sgpa, 2),
        "is_achievable": is_achievable,
        "max_achievable_cgpa": round(max_achievable, 2),
        "guidance": advice
    }

class HigherStudiesService:
    """
    Higher Studies Guidance Service (Requirement F9 & F10):
    - Connects field_of_interest to GATE, CAT/MBA, and UPSC roadmaps.
    - Provides college / PSU shortlists with cutoffs and category transparency.
    - Provides deterministic CGPA maintenance calculations.
    """
    def __init__(self):
        self.gate_engine = GATEReadinessAndShortlistEngine()
        self.mba_engine = MBAMocksShortlistEngine()

    def get_higher_studies_guidance(
        self,
        student: StudentProfile,
        track_type: str = "gate", # 'gate', 'cat', 'upsc'
        target_cgpa: float = 8.0,
        mock_scores: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Returns comprehensive guidance, shortlists, cutoffs, and CGPA maintenance."""
        cgpa_val = float(student.cgpa) if student.cgpa is not None else 8.0
        cgpa_plan = calculate_cgpa_maintenance(
            current_cgpa=cgpa_val,
            current_semester=student.current_semester,
            target_cgpa=target_cgpa
        )

        track_info = {}
        if track_type.lower() in ["gate", "higher_studies", "mtech"]:
            # GATE guidance
            scores = mock_scores or [65.0, 72.0, 78.0]
            pred_band = self.gate_engine.compute_predicted_score_band(scores)
            branch = student.programme_id.replace("BTECH_", "")
            shortlists = self.gate_engine.compute_shortlist_and_tiers(
                student_branch=branch,
                student_cgpa=cgpa_val,
                backlogs=student.backlogs,
                paper_code=branch,
                category="GEN",
                score_band=pred_band
            ) if pred_band else None
            track_info = {
                "track": "GATE / M.Tech & PSU",
                "predicted_score_band": pred_band.model_dump() if pred_band else None,
                "shortlists": shortlists.model_dump() if shortlists else None,
                "psu_cutoffs_reference": "PSUs (e.g. POSOCO, NTPC, BHEL) typically require GATE score 750+ and CGPA >= 7.0."
            }
        elif track_type.lower() in ["cat", "mba"]:
            # MBA guidance
            scores = mock_scores or [85.0, 92.0, 96.0]
            for idx, sc in enumerate(scores):
                self.mba_engine.record_mock(
                    student_id=student.student_id,
                    exam_id="CAT_2026",
                    mock_name=f"Full Mock {idx+1}",
                    raw_score=sc * 2.0,
                    percentile=sc
                )
            band = self.mba_engine.calculate_score_band(student.student_id)
            shortlists = self.mba_engine.generate_shortlist(student.student_id, category="GEN")
            track_info = {
                "track": "CAT / MBA",
                "predicted_cat_percentile": band,
                "shortlists": shortlists,
                "iim_cutoffs_reference": "Top IIMs (A, B, C) evaluate CAT percentile + graduation CGPA (8.0+ recommended for non-engineer diversity or high engineer cutoffs)."
            }
        elif track_type.lower() in ["upsc", "civil_services"]:
            # UPSC guidance
            track_info = {
                "track": "Civil Services (UPSC CSE)",
                "strategy": "Balanced dual-track: Degree completion and CGPA protection first; General Studies (GS I-IV) and Optional in dedicated slots.",
                "core_priority": "Enforce zero backlogs in engineering degree; non-core study throttled during midsem/endsem exams."
            }

        return {
            "student_id": student.student_id,
            "track_type": track_type,
            "cgpa_maintenance": cgpa_plan,
            "track_guidance": track_info
        }

    def generate_balanced_upsc_schedule(
        self,
        student: StudentProfile,
        week_number: int = 1,
        enrolled_course_ids: Optional[List[str]] = None,
        completed_topic_ids: Optional[set] = None
    ) -> WeeklyRoadmap:
        """
        Requirement F10: Balanced UPSC Schedule where core engineering courses take priority
        to guarantee degree protection and zero backlogs, scheduling General Studies in non-core hours.
        """
        return field_planner_engine.plan_weekly_field_topics(
            student=student,
            field_id="FIELD_UPSC",
            week_number=week_number,
            semester_number=student.current_semester,
            enrolled_course_ids=enrolled_course_ids or [],
            completed_topic_ids=completed_topic_ids or set()
        )

higher_studies_service = HigherStudiesService()
