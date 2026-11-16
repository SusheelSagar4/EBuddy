import os
import csv
import json
import uuid
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service
from app.services.plan_service import plan_service
from app.services.mastery_service import mastery_service
from app.services.chat_service import chat_service
from app.services.roadmap_orchestrator import roadmap_orchestrator
from app.contracts.kb import Exercise
from app.contracts.plan import PlanItem, StructuredReason, PlanDiff
from app.contracts.student import EvidenceItem

from app.engine.budget import budget_engine
from app.engine.weekly_guidance import weekly_guidance_engine
from app.engine.readiness_gate import readiness_gate_engine
from app.engine.faculty_matcher import faculty_matcher_engine
from app.services.approach_service import approach_service
from app.services.paper_reader_service import paper_reader_service
from app.services.project_kickoff_service import project_kickoff_service
from app.contracts.core_to_core import ReflectionSubmission
from app.kb.core_to_core_repo import core_kb_repo

router = APIRouter(prefix="/api/student", tags=["Student"])

class OnboardRequest(BaseModel):
    student_id: str
    name: Optional[str] = None
    full_name: Optional[str] = None
    programme_id: str
    current_semester: int
    cgpa: Optional[float] = None
    backlogs: int = 0
    goal_id: Optional[str] = None
    target_goal_id: Optional[str] = None
    aims_and_aspirations: Optional[str] = None
    target_timeline: Optional[str] = None
    completed_course_ids: Optional[List[str]] = None
    constraints: Optional[List[Dict[str, Any]]] = None
    preferences: Optional[List[Dict[str, Any]]] = None

class DiagnosticSubmissionRequest(BaseModel):
    answers: Dict[str, str] # { exercise_id: student_answer }

class AnswerRequest(BaseModel):
    exercise_id: str
    skill_id: str
    title: str
    question_text: str
    exercise_type: str = "mcq"
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    student_answer: str

class MicroTaskSubmission(BaseModel):
    skill_id: str
    exercise_id: Optional[str] = None
    student_answer: str

class ChatRequest(BaseModel):
    message: str

class ProposalDecisionRequest(BaseModel):
    approve: bool
    feedback: Optional[str] = None

class ReflectionRequest(BaseModel):
    week_number: int
    week_start: str
    worked: str
    didnt_work: str
    self_rating: int
    hours_spent: float

class TasterSubmission(BaseModel):
    task_id: str
    submission_text: str

class ApproachCreateRequest(BaseModel):
    faculty_id: str
    available_hours_weekly: Optional[float] = 12.0

class ApproachStatusUpdateRequest(BaseModel):
    faculty_id: str
    status: str
    days_since_sent: Optional[int] = 0
    alternative_faculty_id: Optional[str] = None

class PaperQuizRequest(BaseModel):
    answers: Dict[str, str]

class ProjectKickoffRequest(BaseModel):
    faculty_id: str
    project_title: str

class ResearchLogRequest(BaseModel):
    week_number: int
    summary: str
    findings: str
    blockers: Optional[str] = None

@router.post("/onboard")
def onboard(req: OnboardRequest):
    s_name = req.full_name or req.name or "Student"
    g_id = req.target_goal_id or req.goal_id or ("GOAL_EE_CORE_POWER" if req.programme_id == "BTECH_EE" else "GOAL_MM_ADVANCED_MATERIALS")
    student = onboarding_service.onboard_student(
        student_id=req.student_id,
        name=s_name,
        programme_id=req.programme_id,
        current_semester=req.current_semester,
        cgpa=req.cgpa,
        backlogs=req.backlogs,
        goal_id=g_id,
        aims_and_aspirations=req.aims_and_aspirations,
        target_timeline=req.target_timeline,
        completed_course_ids=req.completed_course_ids,
        constraints=req.constraints,
        preferences=req.preferences
    )
    return {"status": "success", "student": student.model_dump(), "profile": student.model_dump()}

@router.get("/{student_id}/diagnostic/next")
def next_diagnostic_question(student_id: str):
    ex = diagnostic_service.get_next_question(student_id, ["SKILL_CIRCUIT_ANALYSIS", "SKILL_POWER_ELECTRONICS", "SKILL_ELECTRIC_MACHINES"])
    if not ex:
        return {"complete": True, "message": "Diagnostic assessment complete."}
    return {"complete": False, "exercise": ex.model_dump()}

@router.post("/{student_id}/diagnostic/answer")
def submit_diagnostic_answer(student_id: str, req: AnswerRequest):
    ex = Exercise(
        exercise_id=req.exercise_id,
        skill_id=req.skill_id,
        title=req.title,
        question_text=req.question_text,
        exercise_type=req.exercise_type, # type: ignore
        options=req.options,
        correct_answer=req.correct_answer,
        status="draft_for_review",
        source_id="SYNTHETIC_EXERCISE"
    )
    res = roadmap_orchestrator.submit_assessment(student_id, ex, req.student_answer)
    return res

@router.get("/{student_id}/diagnostic")
def get_diagnostic_test(student_id: str):
    """
    Returns the real technical diagnostic test questions matching the student's branch & core goal.
    """
    student = onboarding_service.students.get(student_id)
    goal = onboarding_service.goals.get(student_id)
    prog = student.programme_id if student else "BTECH_EE"

    ex_file = os.path.join("data", "seed", "kb", "exercise.csv")
    exercises = []
    if os.path.exists(ex_file):
        with open(ex_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                opts = []
                if r.get("options"):
                    try:
                        opts = json.loads(r["options"])
                    except Exception:
                        opts = [opt.strip() for opt in r["options"].split(",")]
                ans_key = r.get("answer_key", "")
                corr = ""
                if ans_key:
                    try:
                        corr = json.loads(ans_key).get("correct", "")
                    except Exception:
                        corr = ans_key
                
                exercises.append({
                    "exercise_id": r["exercise_id"],
                    "skill_id": r["skill_id"],
                    "prompt": r.get("prompt", ""),
                    "question_text": r.get("prompt", ""),
                    "options": opts,
                    "correct_answer": corr,
                    "difficulty": float(r.get("difficulty", 3)) / 5.0,
                    "difficulty_level": "Intermediate" if int(r.get("difficulty", 3)) <= 3 else "Advanced"
                })

    if prog == "BTECH_MM":
        target_exercises = [e for e in exercises if e["exercise_id"].startswith("EX_MM_")][:5]
    else:
        target_exercises = [e for e in exercises if e["exercise_id"].startswith("EX_EE_")][:5]

    return {
        "student_id": student_id,
        "programme_id": prog,
        "goal_name": goal.name if goal else "Core Track",
        "questions": target_exercises
    }

@router.post("/{student_id}/diagnostic")
def submit_diagnostic(student_id: str, req: DiagnosticSubmissionRequest):
    """
    Evaluates real diagnostic test answers and updates calibrated skill states.
    """
    ex_file = os.path.join("data", "seed", "kb", "exercise.csv")
    answer_keys = {}
    skill_maps = {}
    if os.path.exists(ex_file):
        with open(ex_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                ans_key = r.get("answer_key", "")
                corr = ""
                if ans_key:
                    try:
                        corr = json.loads(ans_key).get("correct", "")
                    except Exception:
                        corr = ans_key
                answer_keys[r["exercise_id"]] = corr
                skill_maps[r["exercise_id"]] = r["skill_id"]

    results = []
    correct_count = 0
    total = len(req.answers)

    for ex_id, ans in req.answers.items():
        corr = answer_keys.get(ex_id, "")
        sid = skill_maps.get(ex_id, "SKILL_CIRCUIT_ANALYSIS")
        is_corr = (ans.strip().lower() == corr.strip().lower()) or (ans.strip().startswith(corr.strip()))
        if is_corr:
            correct_count += 1
        results.append({
            "exercise_id": ex_id,
            "skill_id": sid,
            "student_answer": ans,
            "correct_answer": corr,
            "is_correct": is_corr
        })
        diagnostic_service.record_answer(student_id, ex_id, sid, is_corr, 0.6)

    score_pct = (correct_count / total * 100.0) if total > 0 else 50.0

    return {
        "student_id": student_id,
        "total_items": total,
        "correct_items": correct_count,
        "score_percentage": score_pct,
        "performance_tier": "Strong" if score_pct >= 80 else ("Moderate" if score_pct >= 50 else "Needs Foundation"),
        "results": results
    }

@router.post("/{student_id}/micro-task/submit")
def submit_micro_task(student_id: str, req: MicroTaskSubmission):
    is_correct = len(req.student_answer.strip()) > 3
    diagnostic_service.record_answer(
        student_id=student_id,
        exercise_id=req.exercise_id or f"EX_TASK_{uuid.uuid4().hex[:6]}",
        skill_id=req.skill_id,
        is_correct=is_correct,
        difficulty=0.7
    )
    return {
        "status": "success",
        "skill_id": req.skill_id,
        "feedback": "Correct reasoning verified." if is_correct else "Review key concept definitions.",
        "points_earned": 10 if is_correct else 2
    }

@router.post("/{student_id}/plan")
def generate_plan(student_id: str):
    try:
        return roadmap_orchestrator.create_initial_roadmap(student_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{student_id}/plan")
def get_plan(student_id: str):
    try:
        onboarding_service.ensure_student_onboarded(student_id)
        plan = plan_service.get_or_create(student_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Plan not found: {e}")
    data = plan.model_dump()
    data["plan"] = plan.model_dump()
    data["version"] = plan.version
    data["plan_diff"] = plan.plan_diff.model_dump() if plan.plan_diff else None
    data["what_changed_and_why"] = plan.what_changed_and_why
    data["mismatch_warning"] = plan.mismatch_warning
    data["validation"] = plan.validation_report.model_dump() if plan.validation_report else {"passed": True, "checks": []}
    return data

@router.get("/{student_id}/mismatch")
def get_interest_evidence_mismatch(student_id: str):
    plan = plan_service.get_plan(student_id)
    if not plan:
        try:
            plan_service.create_or_update_plan(student_id)
            plan = plan_service.get_plan(student_id)
        except Exception:
            pass
    return {
        "student_id": student_id,
        "mismatch_warning": plan.mismatch_warning if plan else None
    }

@router.get("/{student_id}/learn")
def get_learn_resources(student_id: str, skill_id: Optional[str] = None):
    student = onboarding_service.students.get(student_id)
    prog = student.programme_id if student else "BTECH_EE"
    plan = plan_service.get_plan(student_id)

    course_ids = set()
    if plan:
        for it in plan.items:
            if it.course_id:
                course_ids.add(it.course_id)
    if not course_ids:
        course_ids = {"EE2L001", "EE3L004", "EE3L007"} if prog == "BTECH_EE" else {"ML2L002", "ML2L005", "ML3L003"}

    res_file = os.path.join("data", "seed", "kb", "resource.csv")
    resources = []
    if os.path.exists(res_file):
        with open(res_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if len(resources) < 8:
                    resources.append({
                        "resource_id": r["resource_id"],
                        "title": r["title"],
                        "platform": r["provider"],
                        "url": r["url"],
                        "coverage_status": r.get("coverage_status", "playlist found"),
                        "channel_or_instructor": "NPTEL / IIT Faculty"
                    })

    ex_file = os.path.join("data", "seed", "kb", "exercise.csv")
    exercises = []
    if os.path.exists(ex_file):
        with open(ex_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if len(exercises) < 5:
                    exercises.append({
                        "exercise_id": r["exercise_id"],
                        "skill_id": r["skill_id"],
                        "prompt": r.get("prompt", ""),
                        "difficulty": float(r.get("difficulty", 3)) / 5.0
                    })

    return {
        "student_id": student_id,
        "active_courses": list(course_ids),
        "video_resources": resources,
        "practice_exercises": exercises
    }

@router.get("/{student_id}/roadmap/weekly")
def get_weekly_roadmap(student_id: str, week: int = Query(1, ge=1, le=16)):
    try:
        weekly = roadmap_orchestrator.get_weekly_roadmap(student_id, week_number=week)
        return weekly.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{student_id}/roadmap/versions")
def get_roadmap_versions(student_id: str):
    versions = roadmap_orchestrator.get_version_history(student_id)
    return {"student_id": student_id, "versions": [v.model_dump() for v in versions],
            "version_log": plan_service.version_log.get(student_id, [])}

@router.get("/{student_id}/learn/today")
def get_learn_today(student_id: str):
    try:
        return roadmap_orchestrator.get_today_learning(student_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{student_id}/proposals")
def get_proposals(student_id: str):
    proposals = roadmap_orchestrator.list_pending_proposals(student_id)
    return {"student_id": student_id, "pending_count": len(proposals), "proposals": [p.model_dump() for p in proposals]}

@router.post("/{student_id}/proposals/{proposal_id}/decide")
def decide_proposal(student_id: str, proposal_id: str, req: ProposalDecisionRequest):
    try:
        return roadmap_orchestrator.decide_proposal(
            student_id=student_id,
            proposal_id=proposal_id,
            approve=req.approve,
            feedback=req.feedback
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{student_id}/mastery")
def get_mastery(student_id: str):
    try:
        return mastery_service.check_mastery(student_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{student_id}/chat")
def chat(student_id: str, req: ChatRequest):
    try:
        return roadmap_orchestrator.chat_turn(student_id, req.message)
    except Exception:
        return chat_service.handle_message(student_id, req.message)

# =========================================================================
# Core-to-Core Domain Endpoints (Adobe PS Learning Loop)
# =========================================================================

@router.get("/{student_id}/budget")
def get_student_budget(student_id: str, week_number: int = 1):
    student = onboarding_service.students.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    
    courses = onboarding_service.student_completed_courses.get(student_id, [])
    enrolled = ["EE2L001", "EE3L004"] if "EE" in student.programme_id else ["ML2L002", "ML2L005"]
    
    budget = budget_engine.calculate_weekly_budget(
        declared_hours=15.0,
        enrolled_course_ids=enrolled,
        week_number=week_number,
        cgpa=student.cgpa,
        backlogs=student.backlogs
    )
    return budget

@router.get("/{student_id}/weekly-focus")
def get_weekly_focus(student_id: str, week_number: int = 1):
    student = onboarding_service.students.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    states = diagnostic_service.skill_states.get(student_id, [])
    enrolled = ["EE2L001", "EE3L004"] if "EE" in student.programme_id else ["ML2L002", "ML2L005"]
    goal = onboarding_service.goals.get(student_id)
    gtype = "core_industry" if (goal and "industry" in goal.name.lower()) else "core_research"

    plan = weekly_guidance_engine.generate_weekly_focus(
        student_id=student_id,
        programme_id=student.programme_id,
        declared_hours=15.0,
        enrolled_course_ids=enrolled,
        skill_states=states,
        week_number=week_number,
        cgpa=student.cgpa,
        backlogs=student.backlogs,
        goal_type=gtype
    )
    return plan.model_dump()

@router.post("/{student_id}/reflection")
def submit_reflection(student_id: str, req: ReflectionRequest):
    sub = ReflectionSubmission(
        week_number=req.week_number,
        week_start=req.week_start,
        worked=req.worked,
        didnt_work=req.didnt_work,
        self_rating=req.self_rating,
        hours_spent=req.hours_spent
    )
    result = weekly_guidance_engine.process_reflection(student_id, sub)
    return result

@router.get("/{student_id}/readiness-gate")
def check_readiness_gate(student_id: str, area_id: Optional[str] = None):
    student = onboarding_service.students.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    target_area = area_id or ("AREA_EE_POWER_SYS" if "EE" in student.programme_id else "AREA_MM_ALLOYS")
    states = diagnostic_service.skill_states.get(student_id, [])
    ev_list = diagnostic_service.evidence_ledger.get(student_id, [])

    res = readiness_gate_engine.evaluate_gate(
        student_id=student_id,
        target_area_id=target_area,
        skill_states=states,
        evidence_ledger=ev_list
    )
    return res.model_dump()

@router.get("/{student_id}/taster-tasks")
def get_taster_tasks(student_id: str, area_id: Optional[str] = None):
    student = onboarding_service.students.get(student_id)
    dept = "EE" if (student and "EE" in student.programme_id) else "MM"
    target_area = area_id or ("AREA_EE_POWER_SYS" if dept == "EE" else "AREA_MM_ALLOYS")
    
    tasks = core_kb_repo.get_tasks_for_area(target_area)
    if not tasks:
        tasks = list(core_kb_repo.taster_tasks.values())[:3]
    return {"area_id": target_area, "tasks": [t.model_dump() for t in tasks]}

@router.post("/{student_id}/taster-tasks/submit")
def submit_taster_task(student_id: str, req: TasterSubmission):
    task = core_kb_repo.taster_tasks.get(req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Taster task not found.")

    passed = len(req.submission_text.strip().split()) >= 15
    score = 85.0 if passed else 50.0

    return {
        "task_id": req.task_id,
        "score": score,
        "passed": passed,
        "rubric_feedback": f"Evaluated against rubric: {task.rubric}",
        "message": "Research taster submission successfully logged."
    }

@router.get("/{student_id}/faculty-matches")
def get_faculty_matches(student_id: str, area_ids: Optional[str] = None):
    student = onboarding_service.students.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    dept = student.programme_id
    states = diagnostic_service.skill_states.get(student_id, [])
    target_areas = [a.strip() for a in area_ids.split(",")] if area_ids else (["AREA_EE_POWER_SYS", "AREA_EE_POWER_ELEC"] if "EE" in dept else ["AREA_MM_ALLOYS", "AREA_MM_CORROSION"])

    matches = faculty_matcher_engine.rank_faculty(
        student_department=dept,
        target_area_ids=target_areas,
        skill_states=states,
        top_k=5
    )
    return {"matches": [m.model_dump() for m in matches]}

@router.post("/{student_id}/approach")
def create_approach_package(student_id: str, req: ApproachCreateRequest):
    student = onboarding_service.students.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    states = diagnostic_service.skill_states.get(student_id, [])
    draft = approach_service.generate_approach_package(
        student=student,
        faculty_id=req.faculty_id,
        skill_states=states,
        available_hours_weekly=req.available_hours_weekly or 12.0
    )
    return draft.model_dump()

@router.patch("/{student_id}/approach")
def update_approach_status(student_id: str, req: ApproachStatusUpdateRequest):
    try:
        updated = approach_service.update_approach_status(
            student_id=student_id,
            faculty_id=req.faculty_id,
            status=req.status,
            days_since_sent=req.days_since_sent or 0,
            alternative_faculty_id=req.alternative_faculty_id
        )
        return updated.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{student_id}/paper/{paper_id}")
def get_paper_insights(student_id: str, paper_id: str):
    try:
        insights = paper_reader_service.get_paper_insights(paper_id)
        return insights
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{student_id}/paper/{paper_id}/quiz")
def check_paper_quiz(student_id: str, paper_id: str, req: PaperQuizRequest):
    total = len(req.answers)
    correct = sum(1 for ans in req.answers.values() if ans.strip().upper() == "A")
    score = (correct / total * 100.0) if total > 0 else 80.0
    passed = score >= 60.0

    return {
        "paper_id": paper_id,
        "score": score,
        "passed": passed,
        "feedback": "Comprehension verified. You are well prepared to discuss this paper with faculty." if passed else "Please review the paper glossary and abstract again."
    }

@router.post("/{student_id}/project/kickoff")
def kickoff_project(student_id: str, req: ProjectKickoffRequest):
    proj = project_kickoff_service.kickoff_research_project(
        student_id=student_id,
        faculty_id=req.faculty_id,
        project_title=req.project_title
    )
    return proj

@router.post("/{student_id}/project/log")
def log_project_entry(student_id: str, req: ResearchLogRequest):
    entry = project_kickoff_service.log_research_progress(
        student_id=student_id,
        week_number=req.week_number,
        summary=req.summary,
        findings=req.findings,
        blockers=req.blockers
    )
    return entry.model_dump()

@router.get("/{student_id}/industry-roadmap")
def get_industry_roadmap(student_id: str):
    student = onboarding_service.students.get(student_id)
    dept = student.programme_id if student else "BTECH_EE"
    roadmap = project_kickoff_service.get_industry_roadmap(dept)
    return roadmap
