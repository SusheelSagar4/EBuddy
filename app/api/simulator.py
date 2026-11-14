from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.services.adapt_service import adapt_service

router = APIRouter(prefix="/api/sim", tags=["Simulator"])

class QuizSimulationRequest(BaseModel):
    skill_id: str
    score: float # 0.0 to 100.0

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

