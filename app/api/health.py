from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.config import settings

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    table_counts = {}
    try:
        # Check DB connection and count core tables
        queries = {
            "kb_courses": "SELECT COUNT(*) FROM kb.course",
            "kb_slots": "SELECT COUNT(*) FROM kb.programme_requirement",
            "kb_resources": "SELECT COUNT(*) FROM kb.resource",
            "kb_projects": "SELECT COUNT(*) FROM kb.research_project",
            "kb_faculty": "SELECT COUNT(*) FROM kb.faculty",
            "kb_data_issues": "SELECT COUNT(*) FROM kb.data_issue",
            "students": "SELECT COUNT(*) FROM student.student",
            "plans": "SELECT COUNT(*) FROM plan.plan"
        }
        for key, q in queries.items():
            res = db.execute(text(q)).scalar()
            table_counts[key] = res
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "database": db_status,
        "counts": table_counts,
        "configured_llm_model": settings.LLM_MODEL,
        "configured_embedding_model": settings.EMBEDDING_MODEL,
        "telemetry_disabled": not settings.LITELLM_TELEMETRY,
        "local_cost_map": settings.LITELLM_LOCAL_MODEL_COST_MAP
    }

