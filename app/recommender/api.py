"""FastAPI router for EBuddy Course Recommender.

Exposes POST /recommend to provide validated recommendations and explanations.
"""

from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.recommender.engine import recommend
from app.recommender.explain import explain

router = APIRouter(prefix="", tags=["Course Recommendation"])


class RecommendRequest(BaseModel):
    """Course recommendation request payload."""

    branch: str = Field(..., description="Academic branch: 'EE' or 'MME'")
    semester: int = Field(..., ge=1, le=8, description="Current semester (1 to 8)")
    cgpa: float = Field(..., ge=0.0, le=10.0, description="Current cumulative grade point average")
    goal: str = Field(default="", description="Career or learning goal from student profile")
    query: Optional[str] = Field(default=None, description="Optional current user query")
    completed: List[str] = Field(default_factory=list, description="Courses explicitly completed by student")
    avoid: List[str] = Field(default_factory=list, description="Courses student prefers to avoid")
    backlogs: List[str] = Field(default_factory=list, description="Courses with active backlog to exclude from completed")
    overload_approved: bool = Field(default=False, description="Whether FA approval for credit overload is granted")


class RecommendResponse(BaseModel):
    """Course recommendation response payload."""

    answer: str
    llm_used: bool = Field(default=False, description="Whether an LLM was used to generate the explanation")
    llm_error: Optional[str] = Field(default=None, description="Short reason if deterministic template fallback was used")
    data: Dict[str, Any]


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    summary="Recommend eligible courses for this semester",
    description="Deterministically validates prerequisites, credit headroom, and parity offering, then explains recommendations.",
)
def get_recommendations(req: RecommendRequest) -> RecommendResponse:
    """Validate student inputs, run recommendation engine, and return explanation and structured data."""
    clean_branch = req.branch.strip().upper()
    if clean_branch not in ["EE", "MME"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid branch '{req.branch}'. Only 'EE' and 'MME' are currently supported.",
        )

    if req.semester < 1 or req.semester > 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid semester {req.semester}. Semester must be between 1 and 8 inclusive.",
        )

    student_dict = {
        "branch": clean_branch,
        "semester": req.semester,
        "cgpa": req.cgpa,
        "goal": req.goal,
        "completed": req.completed,
        "avoid": req.avoid,
        "backlogs": req.backlogs,
        "overload_approved": req.overload_approved,
    }

    result = recommend(student=student_dict, query=req.query)
    answer, llm_used, llm_error = explain(result=result, student=student_dict)

    return RecommendResponse(
        answer=answer,
        llm_used=llm_used,
        llm_error=llm_error,
        data=result,
    )
