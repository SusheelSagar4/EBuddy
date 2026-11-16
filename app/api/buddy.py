"""
Learning-Buddy API (v2) used by the web UI: profile picker, first-class career tracks, multi-semester
plan, learn/practise, completion-vs-mastery progress. All planning data is deterministic; resource
links, events and questions are read from the knowledge base and are never generated.
"""
import os
import csv
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.kb.track_repo import track_repo, GOAL_TRACKS
from app.personas.registry import persona_registry
from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service
from app.services.plan_service import plan_service
from app.services.mastery_service import mastery_service
from app.engine.skill_state import reliability_tier_for, TIER_WEIGHTS, SOURCE_WEIGHTS
from app.db import persistence
from app.api.validation import validate_new_profile

router = APIRouter(prefix="/api/v2", tags=["Learning Buddy v2"])

GOAL_FAMILY = {
    "GOAL_TRACK_SDE": "SDE", "GOAL_TRACK_DA": "Data Analyst", "GOAL_TRACK_AIML": "AI / ML",
    "GOAL_MBA_CAT": "MBA", "GOAL_UPSC_CSE": "UPSC", "GOAL_STARTUP_FOUNDER": "Startup",
    "GOAL_EE_RES_HIGHER_STUDIES": "Higher Studies", "GOAL_MM_RES_HIGHER_STUDIES": "Higher Studies",
}
LEGACY_GOALS = {"GOAL_CROSS_SDE_DATA", "GOAL_UPSC_COMPETITIVE", "GOAL_TECH_STARTUP"}


class SelectRequest(BaseModel):
    goal_id: Optional[str] = None


class NewStudentRequest(BaseModel):
    student_id: str
    name: str
    programme_id: str
    current_semester: int
    cgpa: Optional[float] = None
    backlogs: int = 0
    goal_id: str
    aims: Optional[str] = None
    weekly_hours_cap: Optional[float] = None
    credit_cap: Optional[float] = None
    completed_course_ids: Optional[List[str]] = None
    interests: Optional[List[str]] = None


class PracticeRequest(BaseModel):
    question_id: str
    answer: str


class EvidenceRequest(BaseModel):
    skill_id: str
    source_type: str
    score: float
    notes: Optional[str] = None


def _family(goal_id: str) -> str:
    if goal_id in GOAL_FAMILY:
        return GOAL_FAMILY[goal_id]
    return "Core"


def _need(student_id: str):
    # ensure_student_onboarded invents a placeholder profile for unknown ids; the web app must get a 404 instead.
    if not onboarding_service.student_exists(student_id):
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found. Pick a profile or create one first.")
    try:
        return onboarding_service.ensure_student_onboarded(student_id)
    except (ValueError, KeyError) as e:  # expected errors only; anything else is a logged 500
        raise HTTPException(status_code=404, detail=str(e))


def _persona_resources(persona_id: str) -> List[Dict[str, Any]]:
    folder = {"btech_upsc": "upsc", "student_startup": "startup"}.get(persona_id)
    if not folder:
        return []
    path = os.path.join("data", "raw", "higher_studies", folder, "resources.csv")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig") as f:
        return [dict(r) for r in csv.DictReader(f)]


@router.get("/students")
def list_students():
    rows = onboarding_service.get_all_synthetic_students()
    for r in rows:
        g = onboarding_service.goal_repo.get_by_id(r.get("goal_id") or "")
        r["goal_name"] = g.name if g else r.get("goal_id")
        r["goal_family"] = _family(r.get("goal_id") or "")
    tags: Dict[str, int] = {}
    for r in rows:
        for t in r.get("edge_case_tags", []):
            tags[t] = tags.get(t, 0) + 1
    return {"count": len(rows), "students": rows, "edge_case_counts": tags, "is_synthetic": True}


@router.get("/goals")
def list_goals(programme_id: Optional[str] = None):
    out = []
    for g in onboarding_service.goal_repo.list_all():
        gid = g.goal_id
        if programme_id == "BTECH_EE" and gid.startswith("GOAL_MM_"):
            continue
        if programme_id in ("BTECH_MM", "BTECH_MME") and gid.startswith("GOAL_EE_"):
            continue
        pkg = persona_registry.for_goal(gid)
        out.append({
            "goal_id": gid, "name": g.name, "category": g.category, "description": g.description, "status": g.status,
            "family": _family(gid), "track_id": GOAL_TRACKS.get(gid) if gid.startswith("GOAL_TRACK_") else None,
            "persona_id": pkg.spec.persona_id if pkg else None, "first_class": pkg is not None and gid not in LEGACY_GOALS,
            "legacy": gid in LEGACY_GOALS, "skill_requirements": len(plan_service.requirements_for(gid)),
        })
    out.sort(key=lambda x: (not x["first_class"], x["family"], x["name"]))
    return {"count": len(out), "goals": out}


@router.get("/tracks")
def list_tracks():
    stats = track_repo.stats()
    return {"tracks": [{
        "track_id": t["track_id"], "goal_id": t["goal_id"], "name": t["name"], "stats": stats[t["track_id"]],
        "phases": [{"phase_id": p["phase_id"], "order": p["order"], "name": p["name"], "objective": p["objective"],
                    "est_hours": p["est_hours"], "hours_basis": p["hours_basis"], "topics": p["topics"][:10],
                    "kb_skills": p["kb_skills"], "resources": len(p["resources"]), "projects": len(p["projects"])} for p in t["phases"]],
    } for t in track_repo.list_tracks()]}


@router.post("/students/{student_id}/select")
def select_student(student_id: str, req: SelectRequest = SelectRequest()):
    """Loads a profile (seed or database), optionally switches the goal, and makes sure a validated plan exists."""
    _need(student_id)
    cur = onboarding_service.goals[student_id].goal_id
    if req.goal_id and req.goal_id != cur:
        if onboarding_service.goal_repo.get_by_id(req.goal_id) is None:
            raise HTTPException(status_code=400, detail=f"Unknown goal {req.goal_id}")
        old = onboarding_service.goals[student_id]
        onboarding_service.switch_goal(student_id, req.goal_id)
        plan_service.create_or_update_plan(student_id, trigger="goal_switch", reasons=[
            f"Goal changed from {old.name} to {onboarding_service.goals[student_id].name} at your request; completed courses and evidence were kept."])
    else:
        plan_service.get_or_create(student_id)
    return overview(student_id)


@router.post("/students")
def create_student(req: NewStudentRequest):
    sid = validate_new_profile(req.student_id, req.name, req.programme_id, req.current_semester, req.cgpa, req.backlogs,
                               req.goal_id, req.completed_course_ids, plan_service.planner.course_info,
                               req.weekly_hours_cap, req.credit_cap)
    if req.student_id != sid:
        req = req.model_copy(update={"student_id": sid})
    cons = []
    if req.weekly_hours_cap:
        cons.append({"constraint_type": "weekly_hours", "parameters": {"max_hours": req.weekly_hours_cap}})
    if req.credit_cap:
        cons.append({"constraint_type": "credit_cap", "parameters": {"max_credits": req.credit_cap}})
    onboarding_service.onboard_student(
        student_id=req.student_id, name=req.name, programme_id=req.programme_id, current_semester=req.current_semester,
        cgpa=req.cgpa, backlogs=req.backlogs, goal_id=req.goal_id, aims_and_aspirations=req.aims,
        completed_course_ids=req.completed_course_ids, constraints=cons,
        interests=[{"topic": t, "weight": 1.0, "reliability_tier": "weak"} for t in (req.interests or [])])
    diagnostic_service.set_ledger(req.student_id, [])
    persistence.upsert_student(dict(student_id=req.student_id, programme_id=req.programme_id, year=(req.current_semester + 1) // 2,
                                    current_semester=req.current_semester, cgpa=req.cgpa or 0.0, persona_tag="manual", name=req.name,
                                    backlogs=req.backlogs, first_year_track="A", edge_case_tags="", aims=req.aims))
    plan_service.create_or_update_plan(req.student_id, trigger="initial")
    return overview(req.student_id)


@router.get("/students/{student_id}/overview")
def overview(student_id: str):
    st = _need(student_id)
    goal = onboarding_service.goals[student_id]
    pkg = persona_registry.for_goal(goal.goal_id)
    cons = plan_service.planner.parse_constraints(onboarding_service.constraints.get(student_id, []))
    plan = plan_service.get_plan(student_id)
    ev = diagnostic_service.evidence_ledger.get(student_id, [])
    tiers = {"strong": 0, "medium": 0, "weak": 0}
    for e in ev:
        tiers[e.reliability_tier or reliability_tier_for(e.source_type)] += 1
    return {
        "student_id": student_id, "name": st.name, "programme_id": st.programme_id, "year": st.year or (st.current_semester + 1) // 2,
        "current_semester": st.current_semester, "cgpa": st.cgpa, "backlogs": st.backlogs,
        "backlog_courses": onboarding_service.backlog_courses.get(student_id, []),
        "completed_count": len(onboarding_service.completed_courses.get(student_id, [])),
        "edge_case_tags": st.edge_case_tags, "aims": onboarding_service.aims_and_aspirations.get(student_id),
        "goal_id": goal.goal_id, "goal_name": goal.name, "goal_family": _family(goal.goal_id),
        "previous_goal_ids": onboarding_service.previous_goals.get(student_id, []),
        "persona_id": pkg.spec.persona_id if pkg else None, "track_id": track_repo.track_id_for_goal(goal.goal_id),
        "weekly_hours_cap": cons["weekly_hours"], "credit_cap": cons["credit_cap"], "avoid_courses": sorted(cons["avoid"]),
        "interests": onboarding_service.interests.get(student_id, []),
        "evidence_by_tier": tiers, "plan_version": plan.version if plan else None, "is_synthetic": True,
    }


@router.get("/students/{student_id}/plan")
def get_plan(student_id: str):
    st = _need(student_id)
    plan = plan_service.get_or_create(student_id)
    goal = onboarding_service.goals[student_id]
    pkg = persona_registry.for_goal(goal.goal_id)
    sems: Dict[int, Dict[str, Any]] = {}
    for it in plan.items:
        s = it.semester_number or st.current_semester
        d = sems.setdefault(s, {"semester_number": s, "is_current": s == st.current_semester, "credits": 0.0,
                                "courses": [], "practice": [], "goal_items": [], "remediation": []})
        row = it.model_dump()
        if it.item_type == "course":
            d["courses"].append(row)
            d["credits"] += it.credits or 0.0
        elif it.item_type == "remediation":
            d["remediation"].append(row)
        elif it.item_type == "exercise" and it.course_id and not it.track_id:
            d["practice"].append(row)
        else:
            d["goal_items"].append(row)
    for d in sems.values():
        d["credits"] = round(d["credits"], 1)
    pointers = []
    if pkg:
        for r in _persona_resources(pkg.spec.persona_id):
            if any(k in (r.get("title", "") + r.get("provider", "")).lower() for k in ("iit bhubaneswar", "startup india", "startup odisha", "upsc")):
                pointers.append({"resource_id": r["resource_id"], "title": r["title"], "provider": r.get("provider"), "url": r.get("url"),
                                 "verified": (r.get("verified", "").upper() == "TRUE"), "note": r.get("note"), "type": r.get("type")})
    return {
        "student_id": student_id, "plan_id": plan.plan_id, "version": plan.version, "goal_id": plan.goal_id, "goal_name": goal.name,
        "goal_family": _family(goal.goal_id), "persona_id": pkg.spec.persona_id if pkg else None,
        "semesters": [sems[k] for k in sorted(sems)],
        "validation": plan.validation_report.model_dump() if plan.validation_report else None,
        "plan_diff": plan.plan_diff.model_dump() if plan.plan_diff else None,
        "what_changed_and_why": plan.what_changed_and_why, "mismatch_warning": plan.mismatch_warning,
        "conflict_flag": plan.conflict_flag, "evidence_summary": plan.evidence_summary, "horizon": plan.horizon,
        "advisories": plan.advisories, "proposals": plan.optional_overload_proposals,
        "versions": plan_service.version_log.get(student_id, []),
        "persona_milestones": pkg.milestones if pkg else [], "official_pointers": pointers,
        "committed_by": "Agent 1 (Roadmap Planner) - deterministic", "total_items": len(plan.items),
    }


@router.post("/students/{student_id}/replan")
def replan(student_id: str):
    _need(student_id)
    res = plan_service.create_or_update_plan(student_id, trigger="manual_regen")
    return {"version": res["version"], "what_changed_and_why": res["what_changed_and_why"], "validation": res["validation"]}


@router.get("/students/{student_id}/learn")
def learn(student_id: str):
    st = _need(student_id)
    plan = plan_service.get_or_create(student_id)
    goal = onboarding_service.goals[student_id]
    planner = plan_service.planner
    course_cards = []
    for it in plan.items:
        if it.item_type != "course" or not it.course_id or (it.semester_number or 0) != st.current_semester:
            continue
        prim = planner.resource_repo.get_primary_resource_for_course(it.course_id)
        backs = planner.resource_repo.get_backup_resources_for_course(it.course_id)
        course_cards.append({
            "course_id": it.course_id, "title": it.title, "credits": it.credits, "why": it.reason.why_this,
            "skills": it.reason.target_skills, "weekly_hours": it.prep_hours_weekly,
            "primary": ({"resource_id": prim.resource_id, "title": prim.title, "provider": prim.provider, "url": prim.url,
                         "coverage_status": prim.coverage_status, "link_verified": prim.link_verified} if prim else None),
            "backups": [{"resource_id": b.resource_id, "title": b.title, "provider": b.provider, "url": b.url,
                         "coverage_status": b.coverage_status} for b in backs],
        })
    remediation = [it.model_dump() for it in plan.items if it.item_type == "remediation"]
    track_block = None
    tid = track_repo.track_id_for_goal(goal.goal_id)
    if tid:
        tr = (plan.horizon or {}).get("track") or {}
        statuses = tr.get("phase_status", [])
        cur = next((p for p in statuses if p["status"] != "demonstrated"), None)
        ph = track_repo.phase(tid, cur["phase_id"]) if cur else None
        hi = tr.get("highest_completed_phase_order", 0)
        ev = track_repo.recommend_events(tid, hi, datetime.now(timezone.utc).strftime("%Y-%m"))
        qs = track_repo.questions(tid)
        skills_needed = [s["skill_id"] for s in (ph or {}).get("kb_skills", [])]
        qs_now = [q for q in qs if q["question_type"] == "mcq" and (not skills_needed or q["kb_skill_id"] in skills_needed)][:5]
        track_block = {
            "track_id": tid, "track_name": track_repo.get(tid)["name"], "phase_status": statuses,
            "schedule": tr.get("schedule", []),
            "current_phase": ({"phase_id": ph["phase_id"], "name": ph["name"], "order": ph["order"], "objective": ph["objective"],
                               "outcome": ph["outcome"], "est_hours": ph["est_hours"], "hours_basis": ph["hours_basis"],
                               "topics": ph["topics"], "resources": ph["resources"][:9], "checkpoints": ph["checkpoints"][:6],
                               "projects": ph["projects"], "pass_threshold_pct": ph["pass_threshold_pct"]} if ph else None),
            "practice_questions": [{"question_id": q["question_id"], "skill": q["track_skill_name"], "kb_skill_id": q["kb_skill_id"],
                                    "difficulty_num": q["difficulty_num"], "stem": q["stem"], "options": sorted(q["options"])} for q in qs_now],
            "practice_problems": track_repo.practice_problems(tid, ph["phase_id"] if ph else None, 6),
            "events": ev,
            "question_bank_note": None if qs else "This track's knowledge base has no auto-gradable question bank yet; checkpoints are logged as timed-quiz or project evidence.",
        }
    pkg = persona_registry.for_goal(goal.goal_id)
    persona_block = None
    if pkg and pkg.spec.persona_id in ("btech_upsc", "student_startup"):
        res = _persona_resources(pkg.spec.persona_id)
        persona_block = {
            "persona_id": pkg.spec.persona_id,
            "milestones": pkg.milestones,
            "resources": [{"resource_id": r["resource_id"], "title": r["title"], "provider": r.get("provider"), "type": r.get("type"),
                           "target_skill": r.get("target_skill"), "url": r.get("url") if r.get("verified", "").upper() == "TRUE" else None,
                           "verified": r.get("verified", "").upper() == "TRUE",
                           "note": r.get("note") if r.get("verified", "").upper() == "TRUE" else "not confirmed yet"} for r in res],
            "incubation_and_club_pointers": [
                {"title": r["title"], "provider": r.get("provider"), "url": r.get("url"), "note": r.get("note")}
                for r in res if r.get("verified", "").upper() == "TRUE" and "iit bhubaneswar" in (r.get("provider", "")).lower()],
            "advisories": pkg.policy.get_advisories(st),
        }
    return {"student_id": student_id, "goal_name": goal.name, "current_semester": st.current_semester, "courses": course_cards,
            "remediation": remediation, "track": track_block, "persona": persona_block,
            "disclaimer": "Every link comes from a knowledge-base row. Links are not yet health-checked (link_verified = false) unless marked."}


@router.post("/students/{student_id}/practice")
def practice(student_id: str, req: PracticeRequest):
    """Grades one track-bank question by option text (position-independent) and records it as assessed evidence."""
    _need(student_id)
    goal = onboarding_service.goals[student_id]
    tid = track_repo.track_id_for_goal(goal.goal_id)
    q = next((x for x in track_repo.questions(tid or "", auto_gradable_only=True) if x["question_id"] == req.question_id), None)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found in this track's bank.")
    correct = req.answer.strip().lower() == q["correct_option_text"].strip().lower()
    before = plan_service.get_or_create(student_id).version
    diagnostic_service.add_evidence(student_id, q["kb_skill_id"], "quiz", 100.0 if correct else 0.0, notes=f"Track question {q['question_id']}")
    persistence.insert_evidence(student_id, q["kb_skill_id"], "quiz", 100.0 if correct else 0.0, "strong", f"Track question {q['question_id']}")
    res = plan_service.create_or_update_plan(student_id, trigger="practice_answer")
    return {"is_correct": correct, "correct_answer": q["correct_option_text"], "explanation": q["explanation"],
            "skill_id": q["kb_skill_id"], "old_version": before, "new_version": res["version"],
            "what_changed_and_why": res["what_changed_and_why"]}


@router.get("/students/{student_id}/progress")
def progress(student_id: str):
    _need(student_id)
    plan_service.get_or_create(student_id)
    m = mastery_service.check_mastery(student_id)
    names = plan_service.planner.skill_names
    ev = sorted(diagnostic_service.evidence_ledger.get(student_id, []), key=lambda e: e.recorded_at, reverse=True)
    return {
        **m,
        "goal_name": onboarding_service.goals[student_id].name,
        "evidence_weights": {"tier_weights": TIER_WEIGHTS, "source_weights": SOURCE_WEIGHTS},
        "evidence": [{"evidence_id": e.evidence_id, "skill_id": e.skill_id, "skill_name": names.get(e.skill_id, e.skill_id),
                      "source_type": e.source_type, "score": e.score, "reliability_tier": e.reliability_tier or reliability_tier_for(e.source_type),
                      "recorded_at": e.recorded_at.isoformat(), "notes": e.notes} for e in ev[:60]],
        "skill_states": [s.model_dump(mode="json") for s in diagnostic_service.skill_states.get(student_id, [])],
    }


@router.post("/students/{student_id}/evidence")
def add_evidence(student_id: str, req: EvidenceRequest):
    """Logs a timed quiz / rubric project / mock interview result and re-plans immediately."""
    _need(student_id)
    allowed = {"timed_quiz", "project_rubric", "mock_interview", "quiz", "exercise", "self_declaration"}
    if req.source_type not in allowed:
        raise HTTPException(status_code=400, detail=f"source_type must be one of {sorted(allowed)}")
    if req.skill_id not in plan_service.planner.skill_names:
        raise HTTPException(status_code=400, detail=f"Unknown skill {req.skill_id}")
    if not 0 <= req.score <= 100:
        raise HTTPException(status_code=400, detail="score must be between 0 and 100")
    before = plan_service.get_or_create(student_id).version
    ev = diagnostic_service.add_evidence(student_id, req.skill_id, req.source_type, req.score, notes=req.notes)
    tier = reliability_tier_for(req.source_type)
    persistence.insert_evidence(student_id, req.skill_id, req.source_type, req.score, tier, req.notes)
    res = plan_service.create_or_update_plan(student_id, trigger=f"evidence:{req.source_type}", reasons=[
        f"New {req.source_type} evidence ({tier} reliability): {req.score:.0f}% on {plan_service.planner.skill_names[req.skill_id]}."])
    return {"evidence_id": ev.evidence_id, "reliability_tier": tier, "old_version": before, "new_version": res["version"],
            "what_changed_and_why": res["what_changed_and_why"], "plan_diff": res["plan_diff"]}
