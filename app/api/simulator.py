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
