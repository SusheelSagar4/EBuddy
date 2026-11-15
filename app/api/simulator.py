from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.services.adapt_service import adapt_service
from app.services.onboarding_service import onboarding_service
from app.services.approach_service import approach_service
from app.services.project_kickoff_service import project_kickoff_service
from app.engine.weekly_guidance import weekly_guidance_engine
from app.engine.faculty_matcher import faculty_matcher_engine
from app.services.diagnostic_service import diagnostic_service

router = APIRouter(prefix="/api/sim", tags=["Simulator"])

class QuizSimulationRequest(BaseModel):
    skill_id: str
    score: float # 0.0 to 100.0

class MidsemStressSimulationRequest(BaseModel):
    week_number: int = 8
    simulated_quiz_score: float = 45.0
    weak_course_id: str = "EE2L001"

class ProfessorNoReplySimulationRequest(BaseModel):
    faculty_id: str
    days_elapsed: int = 11

class GoalPivotSimulationRequest(BaseModel):
    new_goal_type: str # "core_industry" or "core_research"

@router.post("/{student_id}/quiz")
def simulate_quiz_score(student_id: str, req: QuizSimulationRequest):
    """
    Simulator Hook: Injects quiz assessment score for a skill.
    Calculates updated skill state, triggers re-planning, returns PlanDiff and explanation.
    """
    try:
        res = adapt_service.adapt_to_quiz_score(
            student_id=student_id,
            skill_id=req.skill_id,
            score=req.score
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{student_id}/scenario/midsem-stress")
def simulate_midsem_stress(student_id: str, req: MidsemStressSimulationRequest):
    """
    Scenario A: Midsem stress adaptation.
    Simulates low quiz performance in an exam week (e.g. week 8 midsem, calendar factor 0.4).
    The buddy activates CGPA protection, reallocates up to 70-80% of budget to core-course support,
    and returns adapted weekly focus and explanation.
    """
    student = onboarding_service.students.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    states = diagnostic_service.skill_states.get(student_id, [])

    # Generate adapted midsem weekly focus with CGPA protection
    plan = weekly_guidance_engine.generate_weekly_focus(
        student_id=student_id,
        programme_id=student.programme_id,
        declared_hours=15.0,
        enrolled_course_ids=[req.weak_course_id],
        skill_states=states,
        week_number=req.week_number,
        cgpa=student.cgpa,
        backlogs=student.backlogs,
        weak_course_ids=[req.weak_course_id]
    )

    return {
        "scenario": "Midsem Academic Stress & CGPA Protection",
        "student_id": student_id,
        "simulated_quiz_score": req.simulated_quiz_score,
        "calendar_factor": plan.calendar_factor,
        "cgpa_protection_active": plan.cgpa_protection_active,
        "cgpa_protection_reason": plan.cgpa_protection_reason,
        "adjusted_weekly_budget": plan.budget_hours,
        "adapted_weekly_focus": plan.model_dump()
    }

@router.post("/{student_id}/scenario/professor-no-reply")
def simulate_professor_no_reply(student_id: str, req: ProfessorNoReplySimulationRequest):
    """
    Scenario B: Professor no-reply after 10+ days.
    Simulates approaching a professor who has not responded within 10 days.
    The buddy updates status, recommends a polite follow-up draft, and suggests
    the next highest-ranked faculty match.
    """
    student = onboarding_service.students.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    states = diagnostic_service.skill_states.get(student_id, [])
    dept = student.programme_id

    # Rank faculty to find next alternative
    ranked = faculty_matcher_engine.rank_faculty(
        student_department=dept,
        target_area_ids=["AREA_EE_POWER_SYS"] if "EE" in dept else ["AREA_MM_ALLOYS"],
        skill_states=states,
        top_k=5
    )

    alt_faculty = None
    for m in ranked:
        if m.faculty_id != req.faculty_id:
            alt_faculty = m
            break

    alt_id = alt_faculty.faculty_id if alt_faculty else None

    # Update approach status
    draft = approach_service.approaches.get(student_id, {}).get(req.faculty_id)
    if not draft:
        # Create initial draft if not present
        draft = approach_service.generate_approach_package(
            student=student,
            faculty_id=req.faculty_id,
            skill_states=states
        )

    updated_draft = approach_service.update_approach_status(
        student_id=student_id,
        faculty_id=req.faculty_id,
        status="no_reply",
        days_since_sent=req.days_elapsed,
        alternative_faculty_id=alt_id
    )

    followup_draft_text = (
        f"Subject: Re: Prospective Undergraduate Research Inquiry - {student.name}\n\n"
        f"Respected Prof. {updated_draft.faculty_name},\n\n"
        f"I hope you are having a productive week. I am following up on my previous email regarding potential "
        f"undergraduate research opportunities in your laboratory.\n\n"
        f"I remain very enthusiastic about your work and would appreciate 10 minutes of your time during office hours "
        f"if your schedule permits.\n\n"
        f"Thank you for your valuable time.\n\n"
        f"Sincerely,\n{student.name}"
    )

    return {
        "scenario": "Professor Approach 10-Day Follow-Up",
        "student_id": student_id,
        "faculty_id": req.faculty_id,
        "days_elapsed": req.days_elapsed,
        "status": updated_draft.status,
        "followup_recommended": updated_draft.followup_recommended,
        "followup_email_draft": followup_draft_text,
        "alternative_recommendation": alt_faculty.model_dump() if alt_faculty else None,
        "advice": (
            f"It has been {req.days_elapsed} days with no reply from Prof. {updated_draft.faculty_name}. "
            f"You may send a polite follow-up or explore your next best match: {alt_faculty.name if alt_faculty else 'another faculty'}."
        )
    }

@router.post("/{student_id}/scenario/goal-pivot")
def simulate_goal_pivot(student_id: str, req: GoalPivotSimulationRequest):
    """
    Scenario C: Career track pivot between Core Research and Core Industry.
    Swaps roadmap and weekly focus while preserving verified skill states.
    """
    student = onboarding_service.students.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    states = diagnostic_service.skill_states.get(student_id, [])
    dept = student.programme_id

    # Update goal in onboarding
    from app.contracts.goal import Goal
    if req.new_goal_type == "core_industry":
        new_goal = Goal(
            goal_id="GOAL_CORE_INDUSTRY",
            name="Core Industry & PSU Track",
            category="core_industry",
            description="Preparation for GATE, PSU recruitment, and core simulation tool engineering.",
            source_id="CORE_TO_CORE_SEED",
            verified=True
        )
        onboarding_service.goals[student_id] = new_goal
        industry_data = project_kickoff_service.get_industry_roadmap(dept)
        weekly = weekly_guidance_engine.generate_weekly_focus(
            student_id=student_id,
            programme_id=dept,
            declared_hours=15.0,
            enrolled_course_ids=["EE2L001"] if "EE" in dept else ["ML2L002"],
            skill_states=states,
            goal_type="core_industry"
        )
        return {
            "scenario": "Track Pivot to Core Industry / PSU",
            "student_id": student_id,
            "new_goal": new_goal.model_dump(),
            "roadmap": industry_data,
            "weekly_focus": weekly.model_dump()
        }
    else:
        new_goal = Goal(
            goal_id="GOAL_CORE_RESEARCH",
            name="Core Research & Higher Studies Track",
            category="core_research",
            description="Preparation for academic research, faculty mentorship, and international MS/Ph.D.",
            source_id="CORE_TO_CORE_SEED",
            verified=True
        )
        onboarding_service.goals[student_id] = new_goal
        weekly = weekly_guidance_engine.generate_weekly_focus(
            student_id=student_id,
            programme_id=dept,
            declared_hours=15.0,
            enrolled_course_ids=["EE2L001"] if "EE" in dept else ["ML2L002"],
            skill_states=states,
            goal_type="core_research"
        )
        return {
            "scenario": "Track Pivot to Core Research",
            "student_id": student_id,
            "new_goal": new_goal.model_dump(),
            "weekly_focus": weekly.model_dump()
        }

# =============================================================
# Core to MBA Simulator Scenarios (§11 & §14)
# =============================================================

from app.engine.mba_mocks_shortlist import mba_mocks_shortlist_engine
from app.engine.mba_planner import mba_planner_engine
from app.engine.mba_conflict_tracker import mba_conflict_tracker_engine
from app.engine.mba_replan import mba_replan_engine

class StrongVsWeakMockSimulationRequest(BaseModel):
    mock_1_percentile: float = 99.2
    mock_2_percentile: float = 82.0

class VerbalGapSimulationRequest(BaseModel):
    qa_score: float = 92.0
    varc_score: float = 48.0
    dilr_score: float = 70.0

@router.post("/{student_id}/scenario/mba/strong-vs-weak-mock")
def simulate_mba_strong_vs_weak_mock(student_id: str, req: StrongVsWeakMockSimulationRequest = StrongVsWeakMockSimulationRequest()):
    mba_mocks_shortlist_engine.mock_store[student_id] = []
    mba_mocks_shortlist_engine.record_mock(
        student_id=student_id,
        exam_id="MBA-EX-CAT",
        mock_name="AIMCAT 2026 Full Mock 1",
        raw_score=110.0,
        percentile=req.mock_1_percentile,
        date_taken="2026-10-01"
    )
    band_1 = mba_mocks_shortlist_engine.calculate_score_band(student_id)

    mba_mocks_shortlist_engine.record_mock(
        student_id=student_id,
        exam_id="MBA-EX-CAT",
        mock_name="CL Prime Full Mock 2",
        raw_score=72.0,
        percentile=req.mock_2_percentile,
        date_taken="2026-10-15"
    )
    band_2 = mba_mocks_shortlist_engine.calculate_score_band(student_id)
    shortlist_2 = mba_mocks_shortlist_engine.generate_shortlist(student_id, category="GEN")

    return {
        "scenario": "Strong vs Weak Mock Calibration",
        "student_id": student_id,
        "single_mock_status": band_1,
        "two_mocks_calibrated_band": band_2,
        "updated_shortlist": shortlist_2
    }

@router.post("/{student_id}/scenario/verbal-gap")
@router.post("/{student_id}/scenario/mba/verbal-gap")
def simulate_verbal_gap(student_id: str, req: VerbalGapSimulationRequest = VerbalGapSimulationRequest()):
    plan = mba_planner_engine.generate_plan(
        student_id=student_id,
        branch="EE",
        current_cgpa=8.2,
        backlogs=0,
        free_hours_per_week=14.0,
        total_weeks=16,
        verbal_gap=True
    )
    sample_week = plan["weekly_schedule"][2]
    return {
        "scenario": "Verbal-Gap Protocol Activation",
        "student_id": student_id,
        "diagnostic_scores": {"QA": req.qa_score, "VARC": req.varc_score, "DILR": req.dilr_score},
        "verbal_gap_active": plan["verbal_gap_protocol"],
        "sample_week_hours_budget": sample_week["hours_budget"],
        "sample_week_focus_goals": sample_week["focus_goals"],
        "recommended_learning_methods": sample_week["recommended_methods"]
    }

@router.post("/{student_id}/scenario/mba/placement-clash")
def simulate_mba_placement_clash(student_id: str):
    clashes = mba_conflict_tracker_engine.get_known_academic_clashes(semester=7)
    plan = mba_planner_engine.generate_plan(
        student_id=student_id,
        branch="EE",
        current_cgpa=7.8,
        backlogs=0,
        free_hours_per_week=14.0,
        total_weeks=16
    )
    exam_week = plan["weekly_schedule"][13]
    return {
        "scenario": "Semester End-Sem & Placement Clash Mitigation",
        "student_id": student_id,
        "identified_academic_clashes": clashes,
        "end_sem_week_budget": exam_week["hours_budget"],
        "end_sem_alert": exam_week["alert"],
        "end_sem_focus_goals": exam_week["focus_goals"]
    }

@router.post("/{student_id}/scenario/results-below-target")
@router.post("/{student_id}/scenario/mba/results-below-target")
def simulate_results_below_target(student_id: str, percentile: float = 78.5):
    eval_result = mba_replan_engine.evaluate_result(
        student_id=student_id,
        exam_id="MBA-EX-CAT",
        actual_percentile=percentile,
        category="GEN"
    )
    return {
        "scenario": "Results Below Target Strategic Analysis",
        "student_id": student_id,
        "actual_percentile": percentile,
        "status": eval_result["status"],
        "recommendation": eval_result["recommendation"],
        "strategic_actions": eval_result["recommended_actions"],
        "matching_programmes": eval_result["matching_programmes"]
    }

@router.post("/{student_id}/scenario/switch-back-to-core")
@router.post("/{student_id}/scenario/mba/switch-back-to-core")
def simulate_switch_back_to_core(student_id: str, target_route: str = "core_industry"):
    replan_result = mba_replan_engine.switch_back_to_core(
        student_id=student_id,
        target_route=target_route,
        current_plan_version=1,
        reason="Student decided to prioritize core engineering campus placements."
    )
    return {
        "scenario": "Lateral Switch-Back to Core Engineering",
        "student_id": student_id,
        "pivot_result": replan_result
    }

# =============================================================================
# Core to M.Tech Simulation Endpoints (§10)
# =============================================================================

@router.post("/{student_id}/scenario/mtech/strong-vs-weak-mock")
def simulate_mtech_strong_vs_weak_mock(student_id: str):
    from app.engine.gate_readiness_shortlist import gate_readiness_shortlist_engine
    from app.engine.gate_planner import gate_planner_engine

    student = onboarding_service.students.get(student_id)
    dept = student.programme_id if student else "BTECH_EE"
    paper_code = "EE" if "EE" in dept else "MT"
    cgpa = student.cgpa if student else 7.5
    backlogs = student.backlogs if student else 0

    mocks_strong = [760.0, 800.0, 830.0]
    band_strong = gate_readiness_shortlist_engine.compute_predicted_score_band(mocks_strong)
    shortlist_strong = gate_readiness_shortlist_engine.compute_shortlist_and_tiers(
        student_branch=dept,
        student_cgpa=cgpa,
        backlogs=backlogs,
        paper_code=paper_code,
        score_band=band_strong,
        allow_unverified_demo=True
    )
    guidance_strong = gate_planner_engine.generate_weekly_guidance(
        student_id=student_id,
        week_num=10,
        paper_code=paper_code,
        cgpa=cgpa,
        backlogs=backlogs,
        hours_available=16.0,
        current_course_codes=["EE2L001"] if "EE" in dept else ["ML2L001"],
        topic_masteries={"SAMPLE-TOPIC-EE-CIRCUITS": 0.85, "SAMPLE-TOPIC-EE-POWER": 0.80},
        weeks_remaining=8
    )

    mocks_weak = [510.0, 530.0, 520.0]
    band_weak = gate_readiness_shortlist_engine.compute_predicted_score_band(mocks_weak)
    shortlist_weak = gate_readiness_shortlist_engine.compute_shortlist_and_tiers(
        student_branch=dept,
        student_cgpa=cgpa,
        backlogs=backlogs,
        paper_code=paper_code,
        score_band=band_weak,
        allow_unverified_demo=True
    )
    guidance_weak = gate_planner_engine.generate_weekly_guidance(
        student_id=student_id,
        week_num=10,
        paper_code=paper_code,
        cgpa=cgpa,
        backlogs=backlogs,
        hours_available=16.0,
        current_course_codes=["EE2L001"] if "EE" in dept else ["ML2L001"],
        topic_masteries={"SAMPLE-TOPIC-EE-CIRCUITS": 0.45, "SAMPLE-TOPIC-EE-POWER": 0.40},
        weeks_remaining=8
    )

    return {
        "scenario": "Strong vs Weak Mock Comparison (Same Student Profile)",
        "student_id": student_id,
        "branch": dept,
        "paper_code": paper_code,
        "plan_strong": {
            "mock_series": mocks_strong,
            "predicted_score_band": band_strong.model_dump() if band_strong else None,
            "shortlist_summary": {
                "reach_count": len(shortlist_strong.reach),
                "target_count": len(shortlist_strong.target),
                "safe_count": len(shortlist_strong.safe),
                "top_recommendations": shortlist_strong.balanced_recommendation[:3]
            },
            "weekly_focus": guidance_strong["weekly_focus_items"]
        },
        "plan_weak": {
            "mock_series": mocks_weak,
            "predicted_score_band": band_weak.model_dump() if band_weak else None,
            "shortlist_summary": {
                "reach_count": len(shortlist_weak.reach),
                "target_count": len(shortlist_weak.target),
                "safe_count": len(shortlist_weak.safe),
                "top_recommendations": shortlist_weak.balanced_recommendation[:3]
            },
            "weekly_focus": guidance_weak["weekly_focus_items"]
        }
    }

@router.post("/{student_id}/scenario/mtech/placement-clash")
def simulate_mtech_placement_clash(student_id: str):
    from app.engine.gate_conflicts_and_tracker import gate_conflicts_and_tracker_engine
    conflicts = gate_conflicts_and_tracker_engine.detect_conflicts(
        current_week=7,
        placement_active=True,
        placement_window_weeks=(6, 10)
    )
    return {
        "scenario": "Campus Placement vs. GATE Prep Peak Clash",
        "student_id": student_id,
        "current_week": 7,
        "clashes_detected": len(conflicts),
        "alerts": [c.model_dump() for c in conflicts]
    }

@router.post("/{student_id}/scenario/result-below-target")
@router.post("/{student_id}/scenario/mtech/result-below-target")
def simulate_result_below_target(student_id: str, actual_score: float = 490.0):
    from app.engine.gate_interview_and_replan import gate_interview_and_replan_engine
    student = onboarding_service.students.get(student_id)
    dept = student.programme_id if student else "BTECH_EE"
    paper = "EE" if "EE" in dept else "MT"
    cgpa = student.cgpa if student else 7.2
    backlogs = student.backlogs if student else 0

    replan = gate_interview_and_replan_engine.replan_post_result(
        student_id=student_id,
        actual_score=actual_score,
        actual_rank=2850,
        paper_code=paper,
        category="GEN",
        branch=dept,
        cgpa=cgpa,
        backlogs=backlogs
    )
    return {
        "scenario": "Official GATE Result Below Initial Target Programmes",
        "result_data": replan
    }

@router.post("/{student_id}/scenario/route-switch-psu")
@router.post("/{student_id}/scenario/mtech/route-switch-psu")
def simulate_route_switch_psu(student_id: str):
    from app.engine.gate_interview_and_replan import gate_interview_and_replan_engine
    states = diagnostic_service.skill_states.get(student_id, [])
    ev_count = len(states) if states else 8

    switch_data = gate_interview_and_replan_engine.switch_route(
        student_id=student_id,
        from_route="ROUTE_MTECH_INDIA",
        to_route="ROUTE_PSU_GATE",
        current_evidence_count=ev_count
    )
    return {
        "scenario": "Route Transition: M.Tech Higher Studies -> PSU Recruitment",
        "transition": switch_data
    }

# Dynamic Dispatch for Shared Scenario Endpoints
@router.post("/{student_id}/scenario/strong-vs-weak-mock")
def simulate_strong_vs_weak_mock(
    student_id: str,
    track: Optional[str] = None,
    req: Optional[StrongVsWeakMockSimulationRequest] = None
):
    if track == "mba" or (req is not None and (req.mock_1_percentile != 99.2 or req.mock_2_percentile != 82.0)):
        return simulate_mba_strong_vs_weak_mock(student_id, req or StrongVsWeakMockSimulationRequest())
    if track == "mtech":
        return simulate_mtech_strong_vs_weak_mock(student_id)
    student = onboarding_service.students.get(student_id)
    from app.services.plan_service import plan_service
    active_plan = plan_service.get_plan(student_id)
    goal_id = active_plan.goal_id if active_plan else ""
    if "MBA" in goal_id or "MANAGEMENT" in goal_id:
        return simulate_mba_strong_vs_weak_mock(student_id, req or StrongVsWeakMockSimulationRequest())
    return simulate_mtech_strong_vs_weak_mock(student_id)

@router.post("/{student_id}/scenario/placement-clash")
def simulate_placement_clash(student_id: str, track: Optional[str] = None):
    if track == "mba":
        return simulate_mba_placement_clash(student_id)
    if track == "mtech":
        return simulate_mtech_placement_clash(student_id)
    student = onboarding_service.students.get(student_id)
    from app.services.plan_service import plan_service
    active_plan = plan_service.get_plan(student_id)
    goal_id = active_plan.goal_id if active_plan else ""
    if "MBA" in goal_id or "MANAGEMENT" in goal_id:
        return simulate_mba_placement_clash(student_id)
    return simulate_mtech_placement_clash(student_id)
