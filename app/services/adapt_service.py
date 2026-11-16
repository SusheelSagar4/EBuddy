"""
Adaptation service: turns an EVENT (quiz result, course rejection, goal switch) into a new validated
roadmap version plus a PlanDiff and plain-language reasons. Everything is deterministic.

1-click simulator presets (PS 2.4 / Section 5)
    strong_quiz        timed quiz >= 85%  -> practice tested out / track phase skipped, pacing accelerated
    weak_quiz          timed quiz <  40%  -> remedial prerequisite injected, pacing extended
    course_rejection   student rejects a recommended elective -> next-best option of the same slot
    goal_switch        mid-degree goal change -> re-ranked electives + new goal preparation, evidence kept
"""
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.contracts.student import EvidenceItem
from app.contracts.plan import PlanDiff, Plan
from app.engine.skill_state import SkillStateUpdater
from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service
from app.services.plan_service import plan_service, item_label
from app.llm.tasks.explainer import Explainer
from app.db import persistence

PRESETS = {
    "strong_quiz": "Strong Quiz (>= 85%)",
    "weak_quiz": "Weak Quiz (< 40%) + Remedial Prerequisite Injection",
    "course_rejection": "Course Rejection",
    "goal_switch": "Goal Switch",
}


class AdaptService:
    def __init__(self):
        self.state_updater = SkillStateUpdater()
        self.explainer = Explainer()

    # ------------------------------------------------------------------ legacy hook (kept)
    def adapt_to_quiz_score(self, student_id: str, skill_id: str, score: float, source_type: str = "quiz") -> Dict[str, Any]:
        student = onboarding_service.students.get(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not found")
        if 0.0 < score <= 1.0:
            score = score * 100.0  # accept fractions from older clients
        old_plan = plan_service.get_plan(student_id) or plan_service.get_or_create(student_id)
        diagnostic_service.add_evidence(student_id, skill_id, source_type, score, notes="Simulated quiz result")
        persistence.insert_evidence(student_id, skill_id, source_type, score, "strong", "Simulated quiz result")
        reasons = [self._quiz_reason(student_id, skill_id, score)]
        new_plan_data = plan_service.create_or_update_plan(student_id, trigger="simulator:quiz", reasons=reasons)
        new_plan = plan_service.get_plan(student_id)
        diff = new_plan.plan_diff
        return {
            "score": score, "skill_id": skill_id,
            "old_version": old_plan.version, "new_version": new_plan.version,
            "diff": diff.model_dump() if diff else None,
            "explanation": new_plan.what_changed_and_why,
            "new_plan": new_plan_data,
        }

    # ------------------------------------------------------------------ helpers
    def _skill_name(self, sid: str) -> str:
        return plan_service.planner.skill_names.get(sid, sid)

    def _quiz_reason(self, student_id: str, skill_id: str, score: float) -> str:
        st = next((s for s in diagnostic_service.skill_states.get(student_id, []) if s.skill_id == skill_id), None)
        lvl = f"{st.estimated_level:.1f}" if st else "n/a"
        name = self._skill_name(skill_id)
        if score >= 85.0:
            ok = st is not None and st.estimated_level >= 70.0
            return (f"Timed quiz on {name}: {score:.0f}% (strong, assessed evidence). Rule: latest assessed score >= 85% and "
                    f"evidence-weighted level >= 70 (now {lvl}) -> "
                    + ("practice for this skill is tested out and pacing is accelerated; you are not made to repeat what you have shown."
                       if ok else "not yet tested out because earlier results keep the overall level below 70; one more strong result will do it."))
        if score < 40.0:
            return (f"Timed quiz on {name}: {score:.0f}% (strong, assessed evidence). Rule: latest assessed score < 40% -> "
                    f"a remedial prerequisite block for {name} is injected before dependent items (evidence-weighted level now {lvl}).")
        return (f"Timed quiz on {name}: {score:.0f}% (strong, assessed evidence). Between 40% and 85% -> standard pacing; "
                f"evidence-weighted level now {lvl}.")

    def _pick_strong_skill(self, student_id: str, plan: Plan) -> str:
        goal = onboarding_service.goals[student_id]
        req_ids = [r.skill_id for r in plan_service.requirements_for(goal.goal_id)]
        states = {s.skill_id: s for s in diagnostic_service.skill_states.get(student_id, [])}
        st = onboarding_service.students[student_id]
        # a skill whose practice set / track phase is still in the plan, so the effect is visible
        candidates: List[str] = []
        for it in plan.items:
            if it.item_type == "exercise" and (it.semester_number or 0) == st.current_semester and len(it.reason.target_skills) == 1:
                candidates.append(it.reason.target_skills[0])
        tr = (plan.horizon or {}).get("track") or {}
        for ph in tr.get("phase_status", []):
            if ph["status"] != "demonstrated":
                candidates = [s["skill_id"] for s in ph["skills"] if not s["met"]] + candidates
                break
        candidates = [c for c in dict.fromkeys(candidates)] or req_ids or list(states)
        prefer = [c for c in candidates if c in req_ids] or candidates
        return sorted(prefer, key=lambda s: (-(states[s].estimated_level if s in states else 55.0), s))[0]

    def _pick_weak_skill(self, student_id: str) -> str:
        goal = onboarding_service.goals[student_id]
        reqs = sorted(plan_service.requirements_for(goal.goal_id), key=lambda r: (-r.importance, r.skill_id))
        if reqs:
            return reqs[0].skill_id
        states = diagnostic_service.skill_states.get(student_id, [])
        return states[0].skill_id if states else "SKILL_ENGINEERING_MATH"

    def _pick_course_to_reject(self, student_id: str, plan: Plan) -> Optional[str]:
        st = onboarding_service.students[student_id]
        electives = [it for it in plan.items if it.item_type == "course" and it.course_id and it.item_id.startswith("ITEM_ELEC_")]
        electives.sort(key=lambda it: (0 if (it.semester_number or 0) == st.current_semester else 1, it.semester_number or 9, it.course_id))
        return electives[0].course_id if electives else None

    def _default_switch_target(self, student_id: str) -> str:
        st = onboarding_service.students[student_id]
        cur = onboarding_service.goals[student_id].goal_id
        core = "GOAL_MM_ADVANCED_MATERIALS" if "MM" in st.programme_id else "GOAL_EE_CORE_POWER"
        if cur.startswith("GOAL_TRACK_"):
            return core
        return "GOAL_TRACK_SDE"

    # ------------------------------------------------------------------ presets
    def run_preset(self, student_id: str, preset: str, skill_id: Optional[str] = None, score: Optional[float] = None,
                   course_id: Optional[str] = None, goal_id: Optional[str] = None) -> Dict[str, Any]:
        if preset not in PRESETS:
            raise ValueError(f"Unknown preset '{preset}'. Available: {', '.join(PRESETS)}")
        onboarding_service.ensure_student_onboarded(student_id)
        before = plan_service.get_or_create(student_id)
        student = onboarding_service.students[student_id]
        reasons: List[str] = []
        event: Dict[str, Any] = {"preset": preset, "label": PRESETS[preset]}

        if preset in ("strong_quiz", "weak_quiz"):
            strong = preset == "strong_quiz"
            sid = skill_id or (self._pick_strong_skill(student_id, before) if strong else self._pick_weak_skill(student_id))
            sc = float(score) if score is not None else (92.0 if strong else 28.0)
            if strong and sc < 85.0:
                raise ValueError("The strong-quiz preset needs a score of at least 85.")
            if (not strong) and sc >= 40.0:
                raise ValueError("The weak-quiz preset needs a score below 40.")
            prev = next((s.estimated_level for s in diagnostic_service.skill_states.get(student_id, []) if s.skill_id == sid), None)
            diagnostic_service.add_evidence(student_id, sid, "timed_quiz", sc, notes=f"Simulator preset: {PRESETS[preset]}")
            persistence.insert_evidence(student_id, sid, "timed_quiz", sc, "strong", f"Simulator preset: {PRESETS[preset]}")
            reasons.append(self._quiz_reason(student_id, sid, sc))
            event.update({"skill_id": sid, "skill_name": self._skill_name(sid), "score": sc, "evidence_type": "timed_quiz",
                          "reliability_tier": "strong", "level_before": prev})
        elif preset == "course_rejection":
            cid = course_id or self._pick_course_to_reject(student_id, before)
            if not cid:
                raise ValueError("No recommended elective is in the current roadmap to reject (mandatory courses cannot be rejected).")
            item = next((it for it in before.items if it.course_id == cid and it.item_type == "course"), None)
            if item is None:
                raise ValueError(f"{cid} is not in the current roadmap.")
            if not (item.item_id.startswith("ITEM_ELEC_") or item.item_id.startswith("ITEM_MIN_")):
                raise ValueError(f"{cid} is a mandatory degree course and cannot be rejected; only recommended electives can.")
            onboarding_service.add_avoid_course(student_id, cid)
            reasons.append(f"You rejected the recommended elective {cid} {item.title or ''} (Semester {item.semester_number}). "
                           f"Your rejection is a hard constraint: the course is excluded from every future version.")
            event.update({"course_id": cid, "title": item.title, "semester": item.semester_number})
        else:  # goal_switch
            target = goal_id or self._default_switch_target(student_id)
            old_goal = onboarding_service.goals[student_id]
            if target == old_goal.goal_id:
                raise ValueError("The student already has this goal.")
            if not plan_service.goal_repo_has(target):
                raise ValueError(f"Unknown goal '{target}'.")
            new_goal = onboarding_service.switch_goal(student_id, target)
            n_ev = len(diagnostic_service.evidence_ledger.get(student_id, []))
            reasons.append(f"Mid-degree goal switch in Semester {student.current_semester}: {old_goal.name} -> {new_goal.name}. "
                           f"All {len(onboarding_service.completed_courses.get(student_id, []))} completed courses and {n_ev} evidence items are kept; "
                           f"mandatory degree courses do not change.")
            event.update({"from_goal": old_goal.goal_id, "to_goal": new_goal.goal_id, "from_goal_name": old_goal.name, "to_goal_name": new_goal.name})

        res = plan_service.create_or_update_plan(student_id, trigger=f"simulator:{preset}", reasons=reasons)
        after = plan_service.get_plan(student_id)
        diff = after.plan_diff

        # item-level explanations (taken from the planner's own structured reasons)
        why_items: List[Dict[str, Any]] = []
        for it in (diff.added_items if diff else [])[:8]:
            why_items.append({"change": "added", "item": item_label(it), "item_type": it.item_type, "semester": it.semester_number,
                              "why": it.reason.why_this})
        for it in (diff.removed_items if diff else [])[:8]:
            if preset == "course_rejection" and it.course_id == event.get("course_id"):
                w = "Rejected by you (hard constraint)."
            elif it.item_type == "exercise":
                w = "Practice set tested out: assessed evidence already meets the bar for this skill."
            elif it.track_phase_id:
                w = "Track phase demonstrated on assessed evidence, or re-paced for the new goal."
            elif preset == "goal_switch":
                w = "Belonged to the previous goal's elective ranking or preparation track."
            else:
                w = "No longer required after re-planning."
            why_items.append({"change": "removed", "item": item_label(it), "item_type": it.item_type, "semester": it.semester_number, "why": w})
        if preset == "course_rejection" and diff:
            repl = [it for it in diff.added_items if it.item_type == "course" and it.semester_number == event.get("semester")]
            if repl:
                diff_reason = (f"Replacement for the same slot: {item_label(repl[0])} - the next-best option by goal relevance and "
                               f"assessed skill gaps, with prerequisites verified.")
            else:
                diff_reason = "No other eligible option exists for that slot; the slot is left for you to choose, nothing is guessed."
            reasons.append(diff_reason)

        return {
            "preset": preset, "label": PRESETS[preset], "student_id": student_id,
            "event": event,
            "old_version": before.version, "new_version": after.version,
            "plan_diff": diff.model_dump() if diff else None,
            "diff_counts": {"added": len(diff.added_items) if diff else 0, "removed": len(diff.removed_items) if diff else 0,
                            "modified": len(diff.modified_items) if diff else 0},
            "why": list(dict.fromkeys(reasons + (diff.reasons if diff else []))),
            "why_items": why_items,
            "what_changed_and_why": after.what_changed_and_why,
            "validation": res["validation"],
            "mismatch_warning": after.mismatch_warning,
            "advisories": after.advisories,
            "horizon": after.horizon,
            "deterministic": True,
            "llm_used": False,
        }

adapt_service = AdaptService()
