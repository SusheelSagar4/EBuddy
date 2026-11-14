from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.personas.registry import persona_registry
from app.kb.repositories import CourseRepo, SkillRepo, GoalRepo
from app.kb.core_to_core_repo import core_kb_repo
from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service
from app.services.plan_service import plan_service
from app.engine.readiness_gate import readiness_gate_engine
from app.engine.faculty_matcher import faculty_matcher_engine

router = APIRouter(prefix="/api/admin", tags=["Admin"])

class StudentProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    cgpa: Optional[float] = None
    backlogs: Optional[int] = None
    current_semester: Optional[int] = None

class ScoreUpdateRequest(BaseModel):
    skill_id: str
    new_level: float

class FacultyUpdateRequest(BaseModel):
    takes_ug_students: Optional[str] = None
    lab_name: Optional[str] = None
    profile_url: Optional[str] = None

class ReprocessRequest(BaseModel):
    reason: str

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
        "total_goals": len(g_repo.list_all()),
        "total_faculty": len(core_kb_repo.faculty),
        "total_papers": len(core_kb_repo.papers),
        "total_research_areas": len(core_kb_repo.research_areas),
        "total_industry_milestones": len(core_kb_repo.industry_milestones)
    }

@router.get("/faculty")
def list_faculty(department: Optional[str] = None):
    faculty = list(core_kb_repo.faculty.values())
    if department:
        faculty = [f for f in faculty if f.department.upper() == department.upper()]
    return {"count": len(faculty), "faculty": [f.model_dump() for f in faculty]}

@router.patch("/faculty/{faculty_id}")
def update_faculty(faculty_id: str, req: FacultyUpdateRequest):
    fac = core_kb_repo.get_faculty_by_id(faculty_id)
    if not fac:
        raise HTTPException(status_code=404, detail="Faculty not found.")
    
    # Update faculty in memory
    updated_dict = fac.model_dump()
    if req.takes_ug_students is not None:
        updated_dict["takes_ug_students"] = req.takes_ug_students
    if req.lab_name is not None:
        updated_dict["lab_name"] = req.lab_name
    if req.profile_url is not None:
        updated_dict["profile_url"] = req.profile_url

    from app.contracts.core_to_core import Faculty
    core_kb_repo.faculty[faculty_id] = Faculty(**updated_dict)
    return {"status": "success", "faculty": core_kb_repo.faculty[faculty_id].model_dump()}

@router.get("/papers")
def list_papers(limit: int = 20):
    papers = list(core_kb_repo.papers.values())[:limit]
    return {"count": len(papers), "papers": [p.model_dump() for p in papers]}

@router.get("/students")
def list_students():
    students = list(onboarding_service.students.values())
    return {"count": len(students), "students": [s.model_dump() for s in students]}

@router.patch("/students/{student_id}")
def update_student(student_id: str, req: StudentProfileUpdateRequest):
    student = onboarding_service.students.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    
    updated_dict = student.model_dump()
    if req.name is not None:
        updated_dict["name"] = req.name
    if req.cgpa is not None:
        updated_dict["cgpa"] = req.cgpa
    if req.backlogs is not None:
        updated_dict["backlogs"] = req.backlogs
    if req.current_semester is not None:
        updated_dict["current_semester"] = req.current_semester

    from app.contracts.student import StudentProfile
    onboarding_service.students[student_id] = StudentProfile(**updated_dict)

    # Immediately trigger re-processing per hard constraint:
    reprocess_result = trigger_reprocessing(student_id, ReprocessRequest(reason="Admin edited student profile attributes."))
    return {"status": "success", "student": onboarding_service.students[student_id].model_dump(), "reprocess": reprocess_result}

@router.post("/students/{student_id}/reprocess")
def trigger_reprocessing(student_id: str, req: ReprocessRequest):
    """
    Hard constraint: Any edit must trigger re-processing immediately:
    recompute skill state, readiness, matches and the current plan, and save a new plan version with a reason.
    """
    student = onboarding_service.students.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    # 1. Recompute skill states from evidence ledger
    ev_list = diagnostic_service.evidence_ledger.get(student_id, [])
    diagnostic_service.state_updater.update_states(student_id, ev_list)
    states = diagnostic_service.skill_states.get(student_id, [])

    # 2. Recompute readiness gate
    target_area = "AREA_EE_POWER_SYS" if "EE" in student.programme_id else "AREA_MM_ALLOYS"
    gate_result = readiness_gate_engine.evaluate_gate(
        student_id=student_id,
        target_area_id=target_area,
        skill_states=states,
        evidence_ledger=ev_list
    )

    # 3. Recompute faculty matches
    matches = faculty_matcher_engine.rank_faculty(
        student_department=student.programme_id,
        target_area_ids=[target_area],
        skill_states=states,
        top_k=5
    )

    # 4. Save new plan version
    new_plan_info = None
    try:
        new_plan_info = plan_service.create_or_update_plan(student_id)
    except Exception as e:
        new_plan_info = {"status": "skipped", "error": str(e)}

    return {
        "status": "reprocessed",
        "student_id": student_id,
        "reason": req.reason,
        "readiness_gate": gate_result.model_dump(),
        "top_matches_count": len(matches),
        "plan_update": new_plan_info,
        "timestamp": datetime.now().isoformat()
    }
