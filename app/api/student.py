from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service
from app.services.plan_service import plan_service
from app.services.mastery_service import mastery_service
from app.services.chat_service import chat_service
from app.services.roadmap_orchestrator import roadmap_orchestrator
from app.contracts.kb import Exercise

router = APIRouter(prefix="/api/student", tags=["Student"])

class OnboardRequest(BaseModel):
    student_id: str
    name: str
    programme_id: str
    current_semester: int
    cgpa: Optional[float] = None
    backlogs: int = 0
    goal_id: str = "GOAL_EE_CORE_POWER"
    completed_course_ids: Optional[List[str]] = None
    constraints: Optional[List[Dict[str, Any]]] = None
    preferences: Optional[List[Dict[str, Any]]] = None

class AnswerRequest(BaseModel):
    exercise_id: str
    skill_id: str
    title: str
    question_text: str
    exercise_type: str = "mcq"
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    student_answer: str

class ChatRequest(BaseModel):
    message: str

class ProposalDecisionRequest(BaseModel):
    approve: bool
    feedback: Optional[str] = None

@router.post("/onboard")
def onboard(req: OnboardRequest):
    student = onboarding_service.onboard_student(
        student_id=req.student_id,
        name=req.name,
        programme_id=req.programme_id,
        current_semester=req.current_semester,
        cgpa=req.cgpa,
        backlogs=req.backlogs,
        goal_id=req.goal_id,
        completed_course_ids=req.completed_course_ids,
        constraints=req.constraints,
        preferences=req.preferences
    )
    return {"status": "success", "student": student.model_dump()}

@router.get("/{student_id}/diagnostic/next")
def next_diagnostic_question(student_id: str):
    ex = diagnostic_service.get_next_question(student_id, ["SKILL_CIRCUIT_ANALYSIS", "SKILL_POWER_ELECTRONICS", "SKILL_ELECTRIC_MACHINES"])
    if not ex:
        return {"complete": True, "message": "Diagnostic assessment complete."}
    return {"complete": False, "exercise": ex.model_dump()}

@router.post("/{student_id}/diagnostic/answer")
def submit_diagnostic_answer(student_id: str, req: AnswerRequest):
    ex = Exercise(
        exercise_id=req.exercise_id,
        skill_id=req.skill_id,
        title=req.title,
        question_text=req.question_text,
        exercise_type=req.exercise_type, # type: ignore
        options=req.options,
        correct_answer=req.correct_answer,
        status="draft_for_review",
        source_id="SYNTHETIC_EXERCISE"
    )
    # Evaluate via Agent 3 through orchestrator
    res = roadmap_orchestrator.submit_assessment(student_id, ex, req.student_answer)
    return res

@router.post("/{student_id}/plan")
def generate_plan(student_id: str):
    try:
        return roadmap_orchestrator.create_initial_roadmap(student_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{student_id}/plan")
def get_plan(student_id: str):
    plan = plan_service.get_plan(student_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan.model_dump()

@router.get("/{student_id}/roadmap/weekly")
def get_weekly_roadmap(student_id: str, week: int = Query(1, ge=1, le=16)):
    try:
        weekly = roadmap_orchestrator.get_weekly_roadmap(student_id, week_number=week)
        return weekly.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{student_id}/roadmap/versions")
def get_roadmap_versions(student_id: str):
    versions = roadmap_orchestrator.get_version_history(student_id)
    return {"student_id": student_id, "versions": [v.model_dump() for v in versions]}

@router.get("/{student_id}/learn/today")
def get_learn_today(student_id: str):
    try:
        return roadmap_orchestrator.get_today_learning(student_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{student_id}/proposals")
def get_proposals(student_id: str):
    proposals = roadmap_orchestrator.list_pending_proposals(student_id)
    return {"student_id": student_id, "pending_count": len(proposals), "proposals": [p.model_dump() for p in proposals]}

@router.post("/{student_id}/proposals/{proposal_id}/decide")
def decide_proposal(student_id: str, proposal_id: str, req: ProposalDecisionRequest):
    try:
        return roadmap_orchestrator.decide_proposal(
            student_id=student_id,
            proposal_id=proposal_id,
            approve=req.approve,
            feedback=req.feedback
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{student_id}/mastery")
def get_mastery(student_id: str):
    try:
        return mastery_service.check_mastery(student_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{student_id}/chat")
def chat(student_id: str, req: ChatRequest):
    return roadmap_orchestrator.chat_turn(student_id, req.message)
