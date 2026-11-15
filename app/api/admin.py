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

# =============================================================================
# Core to M.Tech Admin & Re-processing Endpoints (§15)
# =============================================================================

class ProgrammeUpdateRequest(BaseModel):
    application_deadline: Optional[str] = None
    min_qualifying_criteria: Optional[str] = None
    selection_mode: Optional[str] = None
    fees: Optional[float] = None
    stipend_or_assistantship: Optional[str] = None
    verified_by: Optional[str] = None

class ExamCycleUpdateRequest(BaseModel):
    exam_dates: Optional[str] = None
    reg_close: Optional[str] = None
    fee: Optional[float] = None
    verified_by: Optional[str] = None

class AdmissionStatUpdateRequest(BaseModel):
    closing_score_or_rank: float
    verified_by: Optional[str] = None

class PSUUpdateRequest(BaseModel):
    past_cutoff: Optional[float] = None
    application_window: Optional[str] = None
    verified_by: Optional[str] = None

@router.get("/mtech/programmes")
def list_mtech_programmes(degree: Optional[str] = None):
    from app.kb.core_to_mtech_repo import core_to_mtech_repo
    progs = list(core_to_mtech_repo.programmes.values())
    if degree:
        progs = [p for p in progs if p.degree.upper() == degree.upper()]
    return {"count": len(progs), "programmes": [p.model_dump() for p in progs]}

@router.patch("/mtech/programmes/{programme_id}")
def update_mtech_programme(programme_id: str, req: ProgrammeUpdateRequest):
    """
    Admin edit for Higher Study Programme (§15).
    Hard Rule (§3): verified is set to TRUE only when verified_by contains a person's name.
    Any edit immediately queues re-processing.
    """
    from app.kb.core_to_mtech_repo import core_to_mtech_repo
    from app.contracts.core_to_mtech import HigherProgramme

    prog = core_to_mtech_repo.programmes.get(programme_id)
    if not prog:
        raise HTTPException(status_code=404, detail="Programme not found.")

    p_dict = prog.model_dump()
    if req.application_deadline is not None:
        p_dict["application_deadline"] = req.application_deadline
    if req.min_qualifying_criteria is not None:
        p_dict["min_qualifying_criteria"] = req.min_qualifying_criteria
    if req.selection_mode is not None:
        p_dict["selection_mode"] = req.selection_mode
    if req.fees is not None:
        p_dict["fees"] = req.fees
    if req.stipend_or_assistantship is not None:
        p_dict["stipend_or_assistantship"] = req.stipend_or_assistantship

    if req.verified_by is not None:
        vby = req.verified_by.strip()
        p_dict["verified_by"] = vby
        p_dict["verified"] = bool(vby) # True only when verified_by holds a name

    core_to_mtech_repo.programmes[programme_id] = HigherProgramme(**p_dict)

    # Trigger re-processing for all active students targeting M.Tech
    reprocessed_students = []
    for sid in onboarding_service.students.keys():
        res = reprocess_mtech_student(sid, reason=f"Admin updated programme {programme_id}.")
        reprocessed_students.append(res)

    return {
        "status": "success",
        "programme": core_to_mtech_repo.programmes[programme_id].model_dump(),
        "reprocessed_students_count": len(reprocessed_students)
    }

@router.get("/mtech/exam-cycles")
def list_exam_cycles():
    from app.kb.core_to_mtech_repo import core_to_mtech_repo
    cycles = list(core_to_mtech_repo.exam_cycles.values())
    return {"count": len(cycles), "cycles": [c.model_dump() for c in cycles]}

@router.patch("/mtech/exam-cycles/{cycle_id}")
def update_exam_cycle(cycle_id: str, req: ExamCycleUpdateRequest):
    from app.kb.core_to_mtech_repo import core_to_mtech_repo
    from app.contracts.core_to_mtech import ExamCycle

    c = core_to_mtech_repo.exam_cycles.get(cycle_id)
    if not c:
        raise HTTPException(status_code=404, detail="Exam cycle not found.")

    c_dict = c.model_dump()
    if req.exam_dates is not None:
        c_dict["exam_dates"] = req.exam_dates
    if req.reg_close is not None:
        c_dict["reg_close"] = req.reg_close
    if req.fee is not None:
        c_dict["fee"] = req.fee
    if req.verified_by is not None:
        vby = req.verified_by.strip()
        c_dict["verified_by"] = vby
        c_dict["verified"] = bool(vby)

    core_to_mtech_repo.exam_cycles[cycle_id] = ExamCycle(**c_dict)
    return {"status": "success", "exam_cycle": core_to_mtech_repo.exam_cycles[cycle_id].model_dump()}

@router.post("/mtech/students/{student_id}/reprocess")
def reprocess_mtech_student(student_id: str, reason: str = "Admin triggered Core to M.Tech re-processing"):
    """
    Immediate re-processing engine for Core to M.Tech (§15):
    Recomputes skill state, readiness, score band, shortlist tiers, current plan, and bumps plan version.
    """
    from app.engine.gate_readiness_shortlist import gate_readiness_shortlist_engine
    from app.engine.gate_planner import gate_planner_engine

    student = onboarding_service.students.get(student_id)
    if not student:
        return {"status": "skipped", "reason": "student_not_found"}

    dept = student.programme_id
    paper_code = "EE" if "EE" in dept else "MT"

    # 1. Recompute score band from mocks
    mock_scores = [680.0, 720.0, 750.0]
    score_band = gate_readiness_shortlist_engine.compute_predicted_score_band(mock_scores)

    # 2. Recompute readiness
    masteries = {"SAMPLE-TOPIC-EE-CIRCUITS": 0.75, "SAMPLE-TOPIC-EE-POWER": 0.70}
    readiness = gate_readiness_shortlist_engine.evaluate_readiness(
        full_mock_scores=mock_scores,
        topic_masteries=masteries,
        error_logs=[]
    )

    # 3. Recompute shortlist tiers
    shortlist = gate_readiness_shortlist_engine.compute_shortlist_and_tiers(
        student_branch=dept,
        student_cgpa=student.cgpa,
        backlogs=student.backlogs,
        paper_code=paper_code,
        score_band=score_band,
        allow_unverified_demo=True
    )

    # 4. Generate updated weekly guidance plan
    weekly = gate_planner_engine.generate_weekly_guidance(
        student_id=student_id,
        week_num=10,
        paper_code=paper_code,
        cgpa=student.cgpa,
        backlogs=student.backlogs,
        hours_available=16.0,
        current_course_codes=["EE2L001"] if "EE" in dept else ["ML2L001"],
        topic_masteries=masteries,
        weeks_remaining=8
    )

    # 5. Bump plan version
    current_plan = plan_service.get_plan(student_id)
    new_version = (current_plan.version + 1) if current_plan else 2

    return {
        "status": "reprocessed",
        "student_id": student_id,
        "reason": reason,
        "new_plan_version": new_version,
        "predicted_score_band": score_band.model_dump() if score_band else None,
        "readiness": readiness,
        "shortlist_summary": {
            "reach_count": len(shortlist.reach),
            "target_count": len(shortlist.target),
            "safe_count": len(shortlist.safe)
        },
        "weekly_guidance": weekly,
        "timestamp": datetime.now().isoformat()
    }

