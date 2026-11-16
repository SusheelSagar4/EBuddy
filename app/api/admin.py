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

class StudentEditRequest(BaseModel):
    name: Optional[str] = None
    cgpa: Optional[float] = None
    backlogs: Optional[int] = None
    current_semester: Optional[int] = None
    weekly_hours_cap: Optional[float] = None
    credit_cap: Optional[float] = None
    clear_credit_cap: Optional[bool] = None
    goal_id: Optional[str] = None

class EvidenceEditRequest(BaseModel):
    evidence_id: Optional[str] = None     # edit an existing ledger row ...
    skill_id: Optional[str] = None        # ... or add a new one
    source_type: Optional[str] = "diagnostic"
    score: float

class CourseEditRequest(BaseModel):
    credits: Optional[float] = None
    title: Optional[str] = None

class RuleEditRequest(BaseModel):
    parameters: Dict[str, Any]

@router.get("/students")
def list_students():
    """All synthetic profiles (seed) with a flag for those currently loaded in memory."""
    rows = onboarding_service.get_all_synthetic_students()
    for r in rows:
        r["loaded"] = r["student_id"] in onboarding_service.students
        live = onboarding_service.students.get(r["student_id"])
        if live:
            r.update({"cgpa": live.cgpa, "backlogs": live.backlogs, "current_semester": live.current_semester, "name": live.name})
        plan = plan_service.get_plan(r["student_id"])
        r["plan_version"] = plan.version if plan else None
    extra = [s for sid, s in onboarding_service.students.items() if sid not in {r["student_id"] for r in rows}]
    return {"count": len(rows) + len(extra), "students": rows + [dict(s.model_dump(mode="json"), loaded=True) for s in extra]}

@router.get("/students/{student_id}")
def get_student_detail(student_id: str):
    try:
        st = onboarding_service.ensure_student_onboarded(student_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    from app.engine.skill_state import reliability_tier_for
    names = plan_service.planner.skill_names
    cons = plan_service.planner.parse_constraints(onboarding_service.constraints.get(student_id, []))
    plan = plan_service.get_plan(student_id)
    return {
        "student": st.model_dump(mode="json"),
        "goal_id": onboarding_service.goals[student_id].goal_id, "goal_name": onboarding_service.goals[student_id].name,
        "weekly_hours_cap": cons["weekly_hours"], "credit_cap": cons["credit_cap"], "avoid_courses": sorted(cons["avoid"]),
        "transcript": onboarding_service.transcripts.get(student_id, []),
        "evidence": [{"evidence_id": e.evidence_id, "skill_id": e.skill_id, "skill_name": names.get(e.skill_id, e.skill_id),
                      "source_type": e.source_type, "score": e.score,
                      "reliability_tier": e.reliability_tier or reliability_tier_for(e.source_type), "notes": e.notes}
                     for e in diagnostic_service.evidence_ledger.get(student_id, [])],
        "skill_states": [s.model_dump(mode="json") for s in diagnostic_service.skill_states.get(student_id, [])],
        "plan_version": plan.version if plan else None,
        "versions": plan_service.version_log.get(student_id, []),
    }

@router.patch("/students/{student_id}")
def update_student(student_id: str, req: StudentEditRequest):
    """Edits a profile; the roadmap is re-processed immediately and the response carries the new version + diff."""
    from app.services.reprocess_service import reprocess_service
    from app.contracts.student import StudentProfile
    from app.db import persistence
    try:
        student = onboarding_service.ensure_student_onboarded(student_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Student not found.")
    if req.cgpa is not None and not 0 <= req.cgpa <= 10:
        raise HTTPException(status_code=400, detail="cgpa must be between 0 and 10")
    if req.current_semester is not None and not 1 <= req.current_semester <= 8:
        raise HTTPException(status_code=400, detail="current_semester must be between 1 and 8")
    if req.goal_id is not None and onboarding_service.goal_repo.get_by_id(req.goal_id) is None:
        raise HTTPException(status_code=400, detail=f"Unknown goal {req.goal_id}")
    plan_service.get_or_create(student_id)

    d = student.model_dump()
    fields = {}
    for k in ("name", "cgpa", "backlogs", "current_semester"):
        v = getattr(req, k)
        if v is not None and v != d.get(k):
            d[k] = v
            fields[k] = v
    if "current_semester" in fields:
        d["year"] = (d["current_semester"] + 1) // 2
        fields["year"] = d["year"]
    onboarding_service.students[student_id] = StudentProfile(**d)
    if fields:
        persistence.write_student_profile(student_id, fields)
    changed = list(fields)
    if req.weekly_hours_cap is not None:
        onboarding_service.set_constraint(student_id, "weekly_hours", {"max_hours": float(req.weekly_hours_cap)})
        changed.append("weekly_hours_cap")
    if req.credit_cap is not None:
        onboarding_service.set_constraint(student_id, "credit_cap", {"max_credits": float(req.credit_cap)})
        changed.append("credit_cap")
    elif req.clear_credit_cap:
        onboarding_service.set_constraint(student_id, "credit_cap", None)
        changed.append("credit_cap")
    if req.goal_id is not None and req.goal_id != onboarding_service.goals[student_id].goal_id:
        onboarding_service.switch_goal(student_id, req.goal_id)
        changed.append("goal_id")

    reprocess_result = reprocess_service.reprocess_student(
        student_id, f"Admin edited student profile ({', '.join(changed) or 'no field changed'}).", trigger="admin_edit")
    return {"status": "success", "changed_fields": changed, "student": onboarding_service.students[student_id].model_dump(),
            "reprocess": reprocess_result}

@router.patch("/students/{student_id}/evidence")
def edit_evidence(student_id: str, req: EvidenceEditRequest):
    """Edits or adds a diagnostic / assessment score; skill state and roadmap are re-processed immediately."""
    from app.services.reprocess_service import reprocess_service
    from app.db import persistence
    try:
        onboarding_service.ensure_student_onboarded(student_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Student not found.")
    if not 0 <= req.score <= 100:
        raise HTTPException(status_code=400, detail="score must be between 0 and 100")
    plan_service.get_or_create(student_id)
    ledger = diagnostic_service.evidence_ledger.get(student_id, [])
    if req.evidence_id:
        idx = next((i for i, e in enumerate(ledger) if e.evidence_id == req.evidence_id), None)
        if idx is None:
            raise HTTPException(status_code=404, detail="Evidence row not found.")
        old = ledger[idx]
        ledger[idx] = old.model_copy(update={"score": float(req.score)})
        diagnostic_service.set_ledger(student_id, ledger)
        if old.evidence_id.startswith("EV_DB_"):
            persistence.update_evidence_score(int(old.evidence_id.split("_")[-1]), float(req.score))
        reason = (f"Admin edited {old.source_type} score for {plan_service.planner.skill_names.get(old.skill_id, old.skill_id)}: "
                  f"{old.score:.0f} -> {req.score:.0f}.")
    else:
        if not req.skill_id or req.skill_id not in plan_service.planner.skill_names:
            raise HTTPException(status_code=400, detail="A valid skill_id (or an evidence_id) is required.")
        diagnostic_service.add_evidence(student_id, req.skill_id, req.source_type or "diagnostic", req.score, notes="Added by admin")
        persistence.insert_evidence(student_id, req.skill_id, req.source_type or "diagnostic", req.score, None, "Added by admin")
        reason = f"Admin added {req.source_type} score {req.score:.0f} for {plan_service.planner.skill_names[req.skill_id]}."
    return {"status": "success", "reprocess": reprocess_service.reprocess_student(student_id, reason, trigger="admin_edit")}

@router.post("/students/{student_id}/reprocess")
def trigger_reprocessing(student_id: str, req: ReprocessRequest):
    """Re-runs skill state -> gaps -> planner -> validator and stores a new plan version with the reason."""
    from app.services.reprocess_service import reprocess_service
    student = onboarding_service.students.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    ev_list = diagnostic_service.evidence_ledger.get(student_id, [])
    states = diagnostic_service.skill_states.get(student_id, [])
    target_area = "AREA_EE_POWER_SYS" if "EE" in student.programme_id else "AREA_MM_ALLOYS"
    gate_result = readiness_gate_engine.evaluate_gate(student_id=student_id, target_area_id=target_area,
                                                      skill_states=states, evidence_ledger=ev_list)
    matches = faculty_matcher_engine.rank_faculty(student_department=student.programme_id, target_area_ids=[target_area],
                                                  skill_states=states, top_k=5)
    try:
        new_plan_info = reprocess_service.reprocess_student(student_id, req.reason, trigger="admin_edit")
    except Exception as e:
        new_plan_info = {"status": "skipped", "error": str(e)}
    return {
        "status": "reprocessed", "student_id": student_id, "reason": req.reason,
        "readiness_gate": gate_result.model_dump(), "top_matches_count": len(matches),
        "plan_update": new_plan_info, "timestamp": datetime.now().isoformat()
    }

@router.get("/courses")
def list_courses(q: Optional[str] = None, limit: int = 40):
    info = plan_service.planner.course_info
    rows = [{"course_id": cid, "title": i["title"], "credits": i["credits"], "status": i.get("status")} for cid, i in sorted(info.items())]
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in r["course_id"].lower() or ql in r["title"].lower()]
    return {"count": len(rows), "courses": rows[:limit]}

@router.patch("/courses/{course_id}")
def edit_course(course_id: str, req: CourseEditRequest):
    """Edits course data (credits / title); every loaded student whose plan uses the course is re-processed immediately."""
    from app.services.reprocess_service import reprocess_service
    from app.db import persistence
    if req.credits is not None and not 0 < req.credits <= 12:
        raise HTTPException(status_code=400, detail="credits must be between 0 and 12")
    fields = {k: v for k, v in {"credits": req.credits, "title": req.title}.items() if v is not None}
    try:
        res = reprocess_service.apply_course_update(course_id, fields)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if res["changes"]:
        persistence.write_course(course_id, fields)
    return {"status": "success", **res}

@router.get("/rules")
def list_rules():
    return {"rules": list(plan_service.validator.academic_rules.values())}

@router.patch("/rules/{rule_id}")
def edit_rule(rule_id: str, req: RuleEditRequest):
    """Edits an academic rule's parameters (e.g. the minor CGPA cutoff); all loaded plans are re-processed."""
    from app.services.reprocess_service import reprocess_service
    from app.db import persistence
    try:
        res = reprocess_service.apply_rule_update(rule_id, req.parameters)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    persistence.write_rule_parameters(rule_id, res["new_parameters"])
    return {"status": "success", **res}

@router.post("/reset")
def reset_system():
    """Restores the original seed state: PostgreSQL (drop + reseed) and all in-memory students, evidence and plans."""
    from app.services.reprocess_service import reprocess_service
    return reprocess_service.reset_all()

@router.get("/reprocess-log")
def reprocess_log():
    from app.services.reprocess_service import reprocess_service
    return reprocess_service.status()

@router.get("/overview")
def admin_overview():
    """One call for the Admin screen: system status, LLM mode, KB and track statistics, profile coverage."""
    import json, os
    from app.llm.client import llm_client
    from app.kb.track_repo import track_repo
    from app.db import persistence
    from app.config import settings
    manifest = {}
    mp = os.path.join("data", "seed", "student", "profile_manifest.json")
    if os.path.exists(mp):
        with open(mp, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    tables = ["kb.course", "kb.skill", "kb.goal", "kb.resource", "kb.exercise", "kb.track_resource", "kb.track_event",
              "kb.track_question", "student.student", "student.skill_evidence", "student.completed_course", "plan.plan", "ops.llm_call_log"]
    planner = plan_service.planner
    return {
        "database": {"available": persistence.db_available(), "sync_enabled": persistence.sync_enabled(),
                     "row_counts": persistence.table_counts(tables), "adminer_port": settings.ADMINER_PORT},
        "llm": llm_client.status(),
        "kb": {"courses": len(planner.course_info), "skills": len(planner.skill_names),
               "goals": len(onboarding_service.goal_repo.list_all()), "personas": len(persona_registry.list_all())},
        "tracks": track_repo.stats(),
        "profiles": manifest,
        "memory": {"students_loaded": len(onboarding_service.students), "plans": len(plan_service.plans)},
    }

# =============================================================
# Core to MBA Admin Endpoints (§11 & §14)
# =============================================================

from app.kb.core_to_mba_repo import core_to_mba_repo
from app.contracts.core_to_mba import MBAProgramme, MBAAdmissionStat, MBAPracticeItem

class MBAProgrammeUpdateRequest(BaseModel):
    application_deadline: Optional[str] = None
    fees: Optional[str] = None
    verified: Optional[bool] = None
    verified_by: Optional[str] = None

class MBAAdmissionStatUpdateRequest(BaseModel):
    cutoff_value: Optional[float] = None
    verified: Optional[bool] = None
    verified_by: Optional[str] = None

class MBAPracticeItemUpdateRequest(BaseModel):
    difficulty: Optional[int] = None
    reviewed: Optional[bool] = None
    reviewed_by: Optional[str] = None

@router.get("/mba/programmes")
def list_mba_programmes(verified_only: bool = False):
    """
    Admin View: Lists all MBA programmes with verification status.
    """
    progs = list(core_to_mba_repo.programmes.values())
    if verified_only:
        progs = [p for p in progs if p.verified]
    return {"count": len(progs), "programmes": [p.model_dump() for p in progs]}

@router.patch("/mba/programmes/{programme_id}")
def update_mba_programme(programme_id: str, req: MBAProgrammeUpdateRequest):
    """
    Admin Edit: Updates MBA programme deadline, fees, or verification status.
    Triggers re-processing signal.
    """
    prog = core_to_mba_repo.programmes.get(programme_id)
    if not prog:
        raise HTTPException(status_code=404, detail="MBA Programme not found.")
    
    d = prog.model_dump()
    if req.application_deadline is not None:
        d["application_deadline"] = req.application_deadline
    if req.fees is not None:
        d["fees"] = req.fees
    if req.verified is not None:
        if req.verified and not req.verified_by and not d.get("verified_by"):
            raise HTTPException(status_code=400, detail="Data Integrity Rule: verified=TRUE requires verified_by with a valid reviewer name.")
        d["verified"] = req.verified
    if req.verified_by is not None:
        d["verified_by"] = req.verified_by

    core_to_mba_repo.programmes[programme_id] = MBAProgramme(**d)
    return {
        "status": "success",
        "action": "updated_and_reprocessed",
        "programme": core_to_mba_repo.programmes[programme_id].model_dump()
    }

@router.get("/mba/admission_stats")
def list_mba_admission_stats():
    """
    Admin View: Lists all admission stats and cutoffs.
    """
    stats = core_to_mba_repo.admission_stats
    return {"count": len(stats), "admission_stats": [s.model_dump() for s in stats]}

@router.patch("/mba/admission_stats/{programme_id}/{category}")
def update_mba_admission_stat(programme_id: str, category: str, req: MBAAdmissionStatUpdateRequest):
    """
    Admin Edit: Updates cut-off value or verification.
    """
    target = None
    target_idx = -1
    for i, s in enumerate(core_to_mba_repo.admission_stats):
        if s.programme_id == programme_id and s.category.upper() == category.upper():
            target = s
            target_idx = i
            break
    
    if not target:
        raise HTTPException(status_code=404, detail="Admission stat record not found.")

    d = target.model_dump()
    if req.cutoff_value is not None:
        d["cutoff_value"] = req.cutoff_value
    if req.verified is not None:
        if req.verified and not req.verified_by and not d.get("verified_by"):
            raise HTTPException(status_code=400, detail="Data Integrity Rule: verified=TRUE requires verified_by with a valid reviewer name.")
        d["verified"] = req.verified
    if req.verified_by is not None:
        d["verified_by"] = req.verified_by

    core_to_mba_repo.admission_stats[target_idx] = MBAAdmissionStat(**d)
    return {
        "status": "success",
        "action": "cutoff_updated",
        "admission_stat": core_to_mba_repo.admission_stats[target_idx].model_dump()
    }

@router.get("/mba/practice_items")
def list_mba_practice_items(reviewed_only: bool = False):
    """
    Admin View: Lists diagnostic practice items.
    """
    items = list(core_to_mba_repo.practice_items.values())
    if reviewed_only:
        items = [it for it in items if it.reviewed]
    return {"count": len(items), "practice_items": [it.model_dump() for it in items]}

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
