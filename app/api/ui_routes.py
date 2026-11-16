import os
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from app.api.deps import require_existing_student
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.api.security import require_admin_token
from app.db.session import get_db
from app.contracts.student import StudentProfile
from app.contracts.goal import Goal
from app.contracts.kb import Exercise
from app.contracts.proposal import ChangeProposal
from app.kb.repositories import CourseRepo, GoalRepo, SkillRepo, ResourceRepo
from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service
from app.services.plan_service import plan_service
from app.services.roadmap_orchestrator import roadmap_orchestrator

logger = logging.getLogger("ebuddy.ui_api")

router = APIRouter(prefix="/api", tags=["UI-Endpoints"], dependencies=[Depends(require_existing_student)])

# In-memory singletons for KB queries
course_repo = CourseRepo()
goal_repo = GoalRepo()
skill_repo = SkillRepo()
resource_repo = ResourceRepo()

# Pydantic schemas
class GenerateRoadmapRequest(BaseModel):
    student_id: str
    goal_id: Optional[str] = None

class DiagnosticStartRequest(BaseModel):
    student_id: str
    goal_id: Optional[str] = None

class DiagnosticAnswerRequest(BaseModel):
    exercise_id: str
    skill_id: str
    student_answer: str

class ChatQueryRequest(BaseModel):
    student_id: str
    message: str

class ProposalDecisionRequest(BaseModel):
    approve: bool
    feedback: Optional[str] = None

def _is_llm_configured() -> bool:
    """Same answer as the LLM gateway itself (model, key and endpoint), so status pages never disagree with it."""
    from app.llm.client import llm_client
    return llm_client.is_configured()

def _decorate_plan(plan_dict: Dict[str, Any], student_id: str) -> Dict[str, Any]:
    """Adds course title, credits, verification status, and KB code badges to each item."""
    items = plan_dict.get("items", [])
    enriched_items = []
    total_credits = 0.0

    for it in items:
        cid = it.get("course_id")
        course = course_repo.get_by_id(cid) if cid else None
        
        status = "draft_for_review"
        credits = 0.0
        title = "Self-Directed Activity"
        
        if course:
            status = getattr(course, "status", "verified")
            credits = float(getattr(course, "credits", 0.0))
            title = course.title
            total_credits += credits

        ex_id = it.get("exercise_id")
        res_id = it.get("resource_id")

        enriched = dict(it)
        enriched["title"] = title
        enriched["credits"] = credits
        enriched["status"] = status
        enriched["kb_code"] = cid or ex_id or res_id or "N/A"
        enriched_items.append(enriched)

    # Group by semester
    semesters: Dict[int, List[Dict[str, Any]]] = {}
    for it in enriched_items:
        s = it.get("semester_number", 1)
        semesters.setdefault(s, []).append(it)

    # Warnings from validator
    val_report = plan_dict.get("validation_report") or {}
    warnings = val_report.get("warnings", [])

    # Pending proposals
    pending = roadmap_orchestrator.list_pending_proposals(student_id)

    return {
        "plan_id": plan_dict.get("plan_id"),
        "student_id": student_id,
        "version": plan_dict.get("version", 1),
        "committed_by": "Agent 1 (Roadmap Planner)",
        "total_items": len(enriched_items),
        "total_credits": total_credits,
        "warnings": warnings,
        "unachievable_explanations": val_report.get("unachievable_requests", []),
        "semesters": [
            {
                "semester_number": s_num,
                "semester_credits": sum(i["credits"] for i in s_items),
                "items": s_items
            }
            for s_num, s_items in sorted(semesters.items())
        ],
        "items": enriched_items,
        "pending_proposals": [p.model_dump() for p in pending]
    }

# -----------------------------------------------------------------------------
# 1. Students Endpoint (Page 1)
# -----------------------------------------------------------------------------
@router.get("/students")
def list_synthetic_students():
    """Lists all synthetic student profiles from data/seed/personas/*/students.csv."""
    students = onboarding_service.get_all_synthetic_students()
    return {
        "count": len(students),
        "students": students
    }

@router.get("/students/{student_id}")
def get_student_details(student_id: str):
    """Returns profile for a specific student."""
    student = onboarding_service.ensure_student_onboarded(student_id)
    completed = onboarding_service.completed_courses.get(student_id, [])
    goal = onboarding_service.goals.get(student_id)
    return {
        "student_id": student.student_id,
        "name": student.name,
        "programme_id": student.programme_id,
        "current_semester": student.current_semester,
        "cgpa": student.cgpa,
        "backlogs": student.backlogs,
        "completed_courses": completed,
        "is_synthetic": True,
        "goal_id": goal.goal_id if goal else None,
        "goal_name": goal.name if goal else None
    }

# -----------------------------------------------------------------------------
# 2. Goals Endpoint (Page 2)
# -----------------------------------------------------------------------------
@router.get("/goals")
def list_goals(programme_id: Optional[str] = Query(None)):
    """
    Returns goals filtered by student's branch plus cross-branch goals.
    Cross-branch goals: GOAL_CROSS_SDE_DATA, GOAL_UPSC_COMPETITIVE, GOAL_TECH_STARTUP.
    """
    all_goals = goal_repo.list_all()
    filtered = []
    
    for g in all_goals:
        gid = g.goal_id
        is_cross = not (gid.startswith("GOAL_EE_") or gid.startswith("GOAL_MM_"))  # career tracks, MBA, UPSC, startup
        
        if not programme_id:
            filtered.append(g)
        elif programme_id == "BTECH_EE":
            if gid.startswith("GOAL_EE_") or is_cross:
                filtered.append(g)
        elif programme_id in ["BTECH_MM", "BTECH_MME"]:
            if gid.startswith("GOAL_MM_") or is_cross:
                filtered.append(g)
        else:
            if is_cross:
                filtered.append(g)

    # Enrich with skill requirements count
    result = []
    for g in filtered:
        reqs = plan_service.goal_requirements.get(g.goal_id, [])
        result.append({
            "goal_id": g.goal_id,
            "name": g.name,
            "category": g.category,
            "description": g.description,
            "status": g.status,
            "source_id": g.source_id,
            "skill_requirements_count": len(reqs)
        })

    return {
        "count": len(result),
        "programme_id": programme_id,
        "goals": result
    }

# -----------------------------------------------------------------------------
# 3. Roadmap Endpoints (Page 3)
# -----------------------------------------------------------------------------
@router.post("/roadmap/generate")
def generate_roadmap(req: GenerateRoadmapRequest):
    """
    Generates deterministic academic roadmap using Agent 1.
    Decorates all courses with title, credits, skill-gap reason, and draft/verified badges.
    """
    # Outside the try: an unknown student is a 404 (app-wide handler), not a generic 400
    onboarding_service.ensure_student_onboarded(req.student_id, req.goal_id)
    try:
        res = roadmap_orchestrator.create_initial_roadmap(req.student_id)
        raw_plan = res.get("plan", {})
        return _decorate_plan(raw_plan, req.student_id)
    except (ValueError, KeyError) as e:  # expected errors only; anything else is a logged 500
        logger.error(f"Error generating roadmap: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/roadmap/{student_id}")
def get_current_roadmap(student_id: str):
    """Returns the student's active roadmap plan."""
    # The router guard has already returned 404 for unknown students, so any failure below is a real error:
    # it is no longer disguised as "No roadmap plan found".
    onboarding_service.ensure_student_onboarded(student_id)
    plan = plan_service.get_plan(student_id)
    if not plan:
        res = roadmap_orchestrator.create_initial_roadmap(student_id)
        return _decorate_plan(res.get("plan", {}), student_id)
    return _decorate_plan(plan.model_dump(), student_id)

# -----------------------------------------------------------------------------
# 4. Diagnostic Quiz Endpoints (Page 4)
# -----------------------------------------------------------------------------
@router.post("/diagnostic/start")
def start_diagnostic(req: DiagnosticStartRequest):
    """Initializes/resets adaptive diagnostic assessment session."""
    onboarding_service.ensure_student_onboarded(req.student_id, req.goal_id)
    diagnostic_service.reset_session(req.student_id)
    return {
        "status": "ready",
        "student_id": req.student_id,
        "message": "Diagnostic assessment initialized."
    }

@router.get("/diagnostic/{student_id}/next")
def get_next_diagnostic(student_id: str):
    """
    Serves next adaptive question driving AdaptiveDiagnostic (app/engine/diagnostic.py).
    One question at a time.
    """
    onboarding_service.ensure_student_onboarded(student_id)
    goal = onboarding_service.goals.get(student_id)
    
    # Candidate skills: the goal's skills that have verified bank items (nothing is generated on the fly)
    reqs = plan_service.requirements_for(goal.goal_id if goal else "")
    bank_skills = {ex.skill_id for ex in diagnostic_service.diagnostic_engine.item_bank}
    candidate_skills = [r.skill_id for r in reqs if r.skill_id in bank_skills]
    uncovered = [r.skill_id for r in reqs if r.skill_id not in bank_skills]
    if not candidate_skills:
        st = onboarding_service.students.get(student_id)
        fallback = ["SKILL_PHYSICAL_METALLURGY", "SKILL_THERMODYNAMICS_MAT"] if (st and "MM" in st.programme_id) else \
                   ["SKILL_CIRCUIT_ANALYSIS", "SKILL_POWER_ELECTRONICS", "SKILL_ELECTRIC_MACHINES"]
        candidate_skills = fallback
    prior = diagnostic_service.get_prior(student_id, candidate_skills)

    state = diagnostic_service.get_diagnostic_state(student_id)
    if state["is_complete"]:
        return {
            "complete": True,
            "message": "Adaptive diagnostic assessment complete.",
            "state": state, "prior": prior, "uncovered_skills": uncovered
        }

    item = diagnostic_service.get_next_question(student_id, candidate_skills)
    if not item:
        return {
            "complete": True,
            "message": "Assessment complete (no further verified items for these skills).",
            "state": state, "prior": prior, "uncovered_skills": uncovered
        }

    return {
        "complete": False,
        "exercise": {
            "exercise_id": item.exercise_id,
            "skill_id": item.skill_id,
            "title": item.title,
            "question_text": item.question_text,
            "exercise_type": item.exercise_type,
            "options": item.options or [],
            "difficulty_0_100": item.difficulty_0_100,
            "status": item.status,
            "source_id": item.source_id
        },
        "state": state, "prior": prior, "uncovered_skills": uncovered, "candidate_skills": candidate_skills
    }

@router.post("/diagnostic/{student_id}/answer")
def submit_diagnostic_answer_ui(student_id: str, req: DiagnosticAnswerRequest):
    """Submits answer, evaluates via CAT engine, updates theta ability and confidence."""
    onboarding_service.ensure_student_onboarded(student_id)
    
    # Grade against the server-side key of the item that was actually served (options were shuffled). The item is
    # consumed: each serve accepts one answer, and items that were never served are refused (no replay, no picking).
    item_ex = diagnostic_service.take_served(student_id, req.exercise_id)
    if not item_ex:
        raise HTTPException(status_code=409, detail=(f"Exercise {req.exercise_id} was not served in your current diagnostic "
                                                     f"session or was already answered. Request the next question."))
    plan_service.get_or_create(student_id)

    res = roadmap_orchestrator.submit_assessment(student_id, item_ex, req.student_answer)
    diagnostic_service.active_sessions.setdefault(student_id, []).append({
        "exercise_id": item_ex.exercise_id, "skill_id": item_ex.skill_id, "answer": req.student_answer,
        "is_correct": res["is_correct"], "score": res["score"], "difficulty": item_ex.difficulty_0_100})
    state = diagnostic_service.get_diagnostic_state(student_id)
    res["diagnostic_state"] = state
    if state["is_complete"]:
        # the diagnostic is assessed (strong) evidence: re-plan as soon as it converges
        rp = plan_service.create_or_update_plan(student_id, trigger="diagnostic_complete",
                                                reasons=[f"Adaptive diagnostic finished after {state['answers_count']} items (ability estimate {state['ability_estimate']})."])
        res["replanned"] = {"version": rp["version"], "what_changed_and_why": rp["what_changed_and_why"]}
    return res

# -----------------------------------------------------------------------------
# 5. Tutor Chat Endpoint (Page 5)
# -----------------------------------------------------------------------------
@router.post("/chat")
def handle_chat_message(req: ChatQueryRequest):
    """
    Processes chat through IntentRouter -> Explainer via app/llm/client.py.
    If LLM key is a placeholder, returns clear 'LLM not configured' message.
    Always includes cited KB codes.
    """
    onboarding_service.ensure_student_onboarded(req.student_id)
    try:
        plan_service.get_or_create(req.student_id)
    except Exception:
        # chat still works without a plan, but a failing planner must be visible
        logger.exception("Could not build a plan for %s before chat", req.student_id)
    llm_ready = _is_llm_configured()

    try:
        chat_res = roadmap_orchestrator.chat_turn(req.student_id, req.message)
    except Exception as e:
        logger.error(f"Chat execution error: {e}")
        chat_res = {
            "inferred_intent": "general_guidance",
            "response": f"I am your academic assistant. Regarding '{req.message}': please refer to your course syllabus and advisor.",
            "proposal": None
        }

    raw_response = chat_res.get("response", "")
    
    # If LLM is not configured, prepend notification
    if not llm_ready:
        banner = "⚠️ [LLM Not Configured] Running in deterministic mode grounded in verified KB curriculum records.\n\n"
        final_response = banner + raw_response
    else:
        final_response = raw_response

    # Extract cited KB codes
    student = onboarding_service.students.get(req.student_id)
    plan = plan_service.get_plan(req.student_id)
    cited_codes = []
    
    if plan:
        for it in plan.items[:5]:
            if it.course_id and it.course_id not in cited_codes:
                cited_codes.append(it.course_id)
    if not cited_codes:
        cited_codes = ["EE1L001", "CS1L001", "MA1L001"] if (student and student.programme_id == "BTECH_EE") else ["ML2L002", "ML2L003", "PH1L001"]

    return {
        "student_id": req.student_id,
        "inferred_intent": chat_res.get("inferred_intent", "curriculum_query"),
        "response": final_response,
        "proposal": chat_res.get("proposal"),
        "cited_kb_codes": cited_codes,
        "llm_configured": llm_ready,
        "llm_used": bool(chat_res.get("llm_used")),
        "guardrail": chat_res.get("guardrail", {"blocked": False, "category": "ok"}),
        "disclaimer": chat_res.get("disclaimer", "Official institutional regulations supersede AI advisories.")
    }

# -----------------------------------------------------------------------------
# 6. Approvals Endpoints (Page 6)
# -----------------------------------------------------------------------------
@router.get("/proposals/{student_id}")
def get_pending_proposals(student_id: str):
    """Lists pending ChangeProposals created by Agents 2, 3, or 4."""
    proposals = roadmap_orchestrator.list_pending_proposals(student_id)
    return {
        "student_id": student_id,
        "pending_count": len(proposals),
        "proposals": [p.model_dump() for p in proposals]
    }

@router.post("/proposals/{student_id}/{proposal_id}/decide")
def decide_proposal_ui(student_id: str, proposal_id: str, req: ProposalDecisionRequest):
    """
    Processes student approval or rejection.
    If approved, triggers Agent 1 to replan and commit Roadmap Version N+1.
    """
    try:
        return roadmap_orchestrator.decide_proposal(
            student_id=student_id,
            proposal_id=proposal_id,
            approve=req.approve,
            feedback=req.feedback
        )
    except (ValueError, KeyError) as e:  # expected errors only; anything else is a logged 500
        logger.error(f"Error deciding proposal {proposal_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# -----------------------------------------------------------------------------
# 7. Admin Endpoints (Page 7)
# -----------------------------------------------------------------------------
@router.get("/admin/status")
def get_admin_status(db: Session = Depends(get_db)):
    """Status panel: DB ok, LLM configured yes/no, data row counts."""
    db_healthy = True
    counts = {}
    try:
        tables = [
            ("kb.course", "kb_courses"),
            ("kb.programme_requirement", "kb_slots"),
            ("kb.resource", "kb_resources"),
            ("kb.exercise", "kb_exercises"),
            ("kb.skill", "kb_skills"),
            ("kb.goal", "kb_goals"),
            ("student.student", "students"),
            ("plan.plan", "plans")
        ]
        for tbl, key in tables:
            cnt = db.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
            counts[key] = cnt
    except Exception as e:
        db_healthy = False
        logger.error(f"DB count error: {e}")

    return {
        "db_healthy": db_healthy,
        "llm_configured": _is_llm_configured(),
        "configured_llm_model": settings.LLM_MODEL,
        "adminer_port": settings.ADMINER_PORT,
        "counts": counts
    }

@router.get("/admin/tables")
def list_available_tables():
    """Returns list of key KB tables viewable in admin."""
    return {
        "tables": [
            "kb.course",
            "kb.programme_requirement",
            "kb.skill",
            "kb.goal",
            "kb.exercise",
            "kb.resource",
            "kb.track_phase",
            "kb.track_resource",
            "kb.track_event",
            "student.student",
            "student.skill_evidence",
            "plan.plan"
        ]
    }

@router.get("/admin/tables/{table_name}")
def get_table_data(table_name: str, db: Session = Depends(get_db)):
    """Read-only viewer returning top 50 rows of selected table."""
    allowed = [
        "kb.course",
        "kb.programme_requirement",
        "kb.skill",
        "kb.goal",
        "kb.exercise",
        "kb.resource",
        "kb.track_phase",
        "kb.track_resource",
        "kb.track_event",
        "student.student",
        "student.skill_evidence",
        "plan.plan"
    ]
    if table_name not in allowed:
        raise HTTPException(status_code=400, detail=f"Table {table_name} is not permitted for preview.")

    try:
        result = db.execute(text(f"SELECT * FROM {table_name} LIMIT 50;"))
        columns = list(result.keys())
        rows = [dict(zip(columns, r)) for r in result.fetchall()]
        return {
            "table": table_name,
            "columns": columns,
            "count": len(rows),
            "rows": rows,
            "source": "database",
        }
    except Exception:
        # The database error is logged, not sent to the browser (it can contain connection details / SQL)
        logger.exception("Table preview of %s failed; falling back to the seed file", table_name)
        simple_name = table_name.split(".")[-1]
        seed_path = Path("data/seed/kb") / f"{simple_name}.csv"
        if seed_path.exists():
            import csv
            with open(seed_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = [row for _, row in zip(range(50), reader)]
                columns = reader.fieldnames or []
                return {
                    "table": table_name,
                    "columns": columns,
                    "count": len(rows),
                    "rows": rows,
                    # say so: these are the original seed rows, not live data (edits since the seed are not shown)
                    "source": "seed_file",
                    "note": "Database unavailable: showing the original seed file, not live data.",
                }
        raise HTTPException(status_code=503, detail="Database unavailable and no seed file exists for this table.")

@router.post("/admin/reload-seed", dependencies=[Depends(require_admin_token)])
def reload_seed_data():
    """Resets PostgreSQL and the in-memory state to the original seed (same as POST /api/admin/reset)."""
    from app.services.reprocess_service import reprocess_service
    res = reprocess_service.reset_all()
    if res["database"]["attempted"] and not res["database"]["ok"]:
        raise HTTPException(status_code=500, detail=f"Seed reset failed: {res['database']['detail']}")
    return {"status": "success", "message": "Seed data reloaded successfully.", "output_summary": res["database"]["detail"], **res}
