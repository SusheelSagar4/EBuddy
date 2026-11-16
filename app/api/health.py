import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.config import settings

router = APIRouter()
logger = logging.getLogger("ebuddy.health")

def _check_health(db: Session):
    db_status = "connected"
    table_counts = {}
    try:
        queries = {
            "kb_courses": "SELECT COUNT(*) FROM kb.course",
            "kb_slots": "SELECT COUNT(*) FROM kb.programme_requirement",
            "kb_resources": "SELECT COUNT(*) FROM kb.resource",
            "kb_exercises": "SELECT COUNT(*) FROM kb.exercise",
            "kb_skills": "SELECT COUNT(*) FROM kb.skill",
            "kb_goals": "SELECT COUNT(*) FROM kb.goal",
            "kb_faculty": "SELECT COUNT(*) FROM kb.faculty",
            "kb_data_issues": "SELECT COUNT(*) FROM kb.data_issue",
            "students": "SELECT COUNT(*) FROM student.student",
            "plans": "SELECT COUNT(*) FROM plan.plan"
        }
        for key, q in queries.items():
            res = db.execute(text(q)).scalar()
            table_counts[key] = res
    except Exception:
        logger.exception("Health check: database query failed")
        db_status = "unhealthy: database query failed (details in the server log)"

    from app.llm.client import llm_client

    return {
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "database": db_status,
        "llm_configured": llm_client.is_configured(),
        "counts": table_counts,
        "configured_llm_model": llm_client.model,
        "configured_embedding_model": llm_client.embedding_model or None,
        "telemetry_disabled": not settings.LITELLM_TELEMETRY,
        "local_cost_map": settings.LITELLM_LOCAL_MODEL_COST_MAP
    }

@router.get("/health")
def health_endpoint(db: Session = Depends(get_db)):
    return _check_health(db)

@router.get("/api/health")
def api_health_endpoint(db: Session = Depends(get_db)):
    return _check_health(db)


