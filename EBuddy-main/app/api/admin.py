from fastapi import APIRouter
from typing import Dict, Any
from app.personas.registry import persona_registry
from app.kb.repositories import CourseRepo, SkillRepo, GoalRepo

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/personas")
def list_personas():
    persona_registry.discover()
    personas = persona_registry.list_all()
    return {
        "count": len(personas),
        "personas": [
            {
                "persona_id": p.spec.persona_id,
                "goal_id": p.spec.goal_id,
                "description": p.spec.description,
                "applicable_programmes": p.spec.applicable_programmes,
                "requirements_count": len(p.requirements),
                "milestones_count": len(p.milestones)
            }
            for p in personas
        ]
    }

@router.get("/stats")
def get_stats():
    c_repo = CourseRepo()
    s_repo = SkillRepo()
    g_repo = GoalRepo()
    return {
        "total_courses": len(c_repo.list_all()),
        "total_skills": len(s_repo.list_all()),
        "total_goals": len(g_repo.list_all())
    }

