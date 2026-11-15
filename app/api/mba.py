from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from app.engine.mba_decision import mba_decision_engine
from app.engine.mba_career_map import mba_career_map_engine
from app.engine.mba_diagnostic import mba_diagnostic_engine
from app.engine.mba_profile_audit import mba_profile_audit_engine
from app.engine.mba_planner import mba_planner_engine
from app.engine.mba_story import mba_story_engine
from app.engine.mba_mocks_shortlist import mba_mocks_shortlist_engine
from app.engine.mba_conflict_tracker import mba_conflict_tracker_engine
from app.engine.mba_interview import mba_interview_engine
from app.engine.mba_replan import mba_replan_engine

router = APIRouter(prefix="/api/mba", tags=["Core to MBA"])

# -------------------------------------------------------------
# Request Models
# -------------------------------------------------------------

class DecisionRequest(BaseModel):
    student_id: str
    student_year: int = 3
    student_sem: int = 6
    student_branch: str = "EE"
    student_cgpa: float = 8.0
    backlogs: int = 0
    chosen_option: Optional[str] = None

class DiagnosticStartRequest(BaseModel):
    student_id: str
    exam_id: str = "MBA-EX-CAT"

class DiagnosticAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    user_answer: str

class ProfileAuditRequest(BaseModel):
    student_id: str
    branch: str = "EE"
    cgpa: float = 8.0
    backlogs: int = 0
    projects: Optional[List[Dict[str, Any]]] = None
    internships: Optional[List[Dict[str, Any]]] = None
    leadership_roles: Optional[List[str]] = None
    extracurriculars: Optional[List[str]] = None
    work_ex_plan: Optional[str] = None

class PlanGenerationRequest(BaseModel):
    student_id: str
    branch: str = "EE"
    current_cgpa: float = 8.0
    backlogs: int = 0
    free_hours_per_week: float = 14.0
    total_weeks: int = 16
    target_exam_id: str = "MBA-EX-CAT"
    verbal_gap: bool = False
    profile_actions: Optional[List[str]] = None
    completed_course_ids: Optional[List[str]] = None

class StoryEvaluationRequest(BaseModel):
    student_id: str
    kind: str # why_mba, why_not_core, project_story, internship_story
    text: str
    branch: str = "EE"

class MockRecordRequest(BaseModel):
    student_id: str
    exam_id: str = "MBA-EX-CAT"
    mock_name: str
    raw_score: float
    percentile: float
    section_scores: Optional[Dict[str, float]] = None
    date_taken: Optional[str] = None

class ChecklistUpdateRequest(BaseModel):
    item_id: str
    completed: bool

class InterviewStartRequest(BaseModel):
    student_id: str
    branch: str = "EE"

class InterviewAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer_text: str

class WATEvaluationRequest(BaseModel):
    student_id: str
    topic_id: str
    essay_text: str

class ResultEvaluationRequest(BaseModel):
    student_id: str
    exam_id: str = "MBA-EX-CAT"
    actual_percentile: float
    category: str = "GEN"

class SwitchBackRequest(BaseModel):
    student_id: str
    target_route: str = "core_industry"
    current_plan_version: int = 1
    reason: str = "Strategic shift back to core engineering campus placement"

# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------

# 1. Decision & Comparative Timelines
@router.post("/decision")
def get_decision_options(req: DecisionRequest):
    options = mba_decision_engine.build_decision_options(
        student_id=req.student_id,
        student_year=req.student_year,
        student_sem=req.student_sem,
        student_branch=req.student_branch,
        student_cgpa=req.student_cgpa,
        backlogs=req.backlogs
    )
    result = {"student_id": req.student_id, "options": [o.model_dump() for o in options]}
    if req.chosen_option:
        rec = mba_decision_engine.record_choice(req.student_id, req.chosen_option)
        result["recorded_choice"] = rec
    return result

# 2. Career Map
@router.get("/career-map")
def get_career_map(branch: str = Query("EE"), include_general: bool = Query(True)):
    paths = mba_career_map_engine.get_career_paths(branch=branch, include_general=include_general)
    advantage = mba_career_map_engine.get_engineering_advantage(branch=branch)
    return {
        "branch": branch,
        "count": len(paths),
        "engineering_advantage": advantage,
        "paths": [p.model_dump() for p in paths]
    }

# 3. Diagnostic & Profile Audit
@router.post("/diagnostic/start")
def start_diagnostic(req: DiagnosticStartRequest):
    try:
        return mba_diagnostic_engine.start_diagnostic(req.student_id, req.exam_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/diagnostic/answer")
def submit_diagnostic_answer(req: DiagnosticAnswerRequest):
    try:
        return mba_diagnostic_engine.submit_answer(req.session_id, req.question_id, req.user_answer)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/diagnostic/report/{session_id}")
def get_diagnostic_report(session_id: str):
    try:
        return mba_diagnostic_engine.get_report(session_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/profile-audit")
def evaluate_profile(req: ProfileAuditRequest):
    return mba_profile_audit_engine.evaluate_profile(
        student_id=req.student_id,
        branch=req.branch,
        cgpa=req.cgpa,
        backlogs=req.backlogs,
        projects=req.projects,
        internships=req.internships,
        leadership_roles=req.leadership_roles,
        extracurriculars=req.extracurriculars,
        work_ex_plan=req.work_ex_plan
    )

# 4. Weekly Guidance & Pacing Planner
@router.post("/plan")
def generate_prep_plan(req: PlanGenerationRequest):
    try:
        return mba_planner_engine.generate_plan(
            student_id=req.student_id,
            branch=req.branch,
            current_cgpa=req.current_cgpa,
            backlogs=req.backlogs,
            free_hours_per_week=req.free_hours_per_week,
            total_weeks=req.total_weeks,
            target_exam_id=req.target_exam_id,
            verbal_gap=req.verbal_gap,
            profile_actions=req.profile_actions,
            completed_course_ids=req.completed_course_ids
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 5. Story Builder (Authoring critique, NO ghostwriting)
@router.post("/story/evaluate")
def evaluate_story_draft(req: StoryEvaluationRequest):
    return mba_story_engine.evaluate_draft(
        student_id=req.student_id,
        kind=req.kind,
        text=req.text,
        branch=req.branch
    )

# 6. Mocks & Shortlist Tiering
@router.post("/mocks/record")
def record_mock(req: MockRecordRequest):
    return mba_mocks_shortlist_engine.record_mock(
        student_id=req.student_id,
        exam_id=req.exam_id,
        mock_name=req.mock_name,
        raw_score=req.raw_score,
        percentile=req.percentile,
        section_scores=req.section_scores,
        date_taken=req.date_taken
    )

@router.get("/mocks/band/{student_id}")
def get_mock_band(student_id: str):
    return mba_mocks_shortlist_engine.calculate_score_band(student_id)

@router.get("/shortlist/{student_id}")
def get_shortlist(
    student_id: str,
    category: str = Query("GEN"),
    target_exam_id: str = Query("MBA-EX-CAT"),
    preliminary_percentile: Optional[float] = Query(None)
):
    return mba_mocks_shortlist_engine.generate_shortlist(
        student_id=student_id,
        category=category,
        target_exam_id=target_exam_id,
        preliminary_percentile=preliminary_percentile
    )

# 7. Conflicts & Application Tracker
@router.get("/conflicts")
def get_known_conflicts(semester: int = Query(7)):
    return {"semester": semester, "clashes": mba_conflict_tracker_engine.get_known_academic_clashes(semester)}

@router.get("/checklist/{student_id}")
def get_checklist(student_id: str, category: str = Query("GEN")):
    return mba_conflict_tracker_engine.get_application_checklist(student_id, category)

@router.post("/checklist/{student_id}/update")
def update_checklist_item(student_id: str, req: ChecklistUpdateRequest):
    return mba_conflict_tracker_engine.update_checklist_item(student_id, req.item_id, req.completed)

@router.get("/deadlines")
def get_official_deadlines():
    return {"deadlines": mba_conflict_tracker_engine.get_verified_deadlines()}

# 8. Interview Prep & WAT
@router.get("/interview/topics")
def get_interview_topics(branch: str = Query("EE")):
    return {
        "branch": branch,
        "topics": [t.model_dump() for t in mba_interview_engine.get_branch_topics(branch)],
        "general_questions": [q.model_dump() for q in mba_interview_engine.get_general_pi_questions()],
        "wat_topics": [w.model_dump() for w in mba_interview_engine.get_wat_topics()]
    }

@router.post("/interview/start")
def start_interview_session(req: InterviewStartRequest):
    return mba_interview_engine.start_mock_pi_session(req.student_id, req.branch)

@router.post("/interview/answer")
def submit_interview_answer(req: InterviewAnswerRequest):
    try:
        return mba_interview_engine.evaluate_response(req.session_id, req.question_id, req.answer_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/wat/evaluate")
def evaluate_wat_essay(req: WATEvaluationRequest):
    return mba_interview_engine.evaluate_wat_essay(req.student_id, req.topic_id, req.essay_text)

# 9. Post-Result & Switch-Back to Core
@router.post("/replan/result")
def evaluate_result(req: ResultEvaluationRequest):
    return mba_replan_engine.evaluate_result(
        student_id=req.student_id,
        exam_id=req.exam_id,
        actual_percentile=req.actual_percentile,
        category=req.category
    )

@router.post("/replan/switch-back")
def switch_back_to_core(req: SwitchBackRequest):
    try:
        return mba_replan_engine.switch_back_to_core(
            student_id=req.student_id,
            target_route=req.target_route,
            current_plan_version=req.current_plan_version,
            reason=req.reason
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
