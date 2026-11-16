"""
Plan service: the single place where a student's roadmap version is built, validated, diffed,
explained and stored. Building is delegated to Agent 1 (the sole roadmap writer); everything here
is deterministic - the LLM is never asked to choose courses or schedule anything.
"""
import os
import csv
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from app.contracts.goal import GoalRequirement
from app.contracts.plan import Plan, PlanItem, PlanDiff
from app.engine.gaps import GapAnalyzer
from app.agents.agent_1_planner import RoadmapPlannerAgent
from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service
from app.db import persistence


def item_key(it: PlanItem) -> Tuple[str, str]:
    ident = it.course_id or it.resource_id or it.track_phase_id or it.exercise_id or it.title or it.item_id
    if it.item_type in ("exercise", "remediation", "milestone") and (it.course_id or it.track_phase_id):
        ident = f"{ident}|{it.reason.intent.split(':')[0][:24]}"
    return (it.item_type, str(ident))


def item_label(it: PlanItem) -> str:
    if it.item_type == "course" and it.course_id:
        return f"{it.course_id} {it.title or ''}".strip()
    return it.title or it.course_id or it.resource_id or it.item_id


class PlanService:
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self.agent_1 = RoadmapPlannerAgent(seed_dir)          # sole writer of roadmap versions
        self.planner = self.agent_1.planner_engine
        self.validator = self.agent_1.validator_engine
        self.gap_analyzer = GapAnalyzer()
        self.plans: Dict[str, Plan] = {}
        self.plan_history: Dict[str, List[Plan]] = {}
        self.version_log: Dict[str, List[Dict[str, Any]]] = {}
        self.input_snapshots: Dict[str, Dict[str, Any]] = {}
        self.goal_requirements: Dict[str, List[GoalRequirement]] = {}
        self._load_requirements()

    def _load_requirements(self):
        self.goal_requirements.clear()
        path = os.path.join(self.seed_dir, "goal_skill_requirement.csv")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    gid = r["goal_id"]
                    self.goal_requirements.setdefault(gid, []).append(GoalRequirement(
                        goal_id=gid, skill_id=r["skill_id"], required_level=float(r["required_level"]),
                        importance=float(r.get("importance", 1.0)), source_id=r.get("source_id", "DESIGN_TEAM")))

    def reset(self):
        self.plans.clear(); self.plan_history.clear(); self.version_log.clear(); self.input_snapshots.clear()

    def requirements_for(self, goal_id: str) -> List[GoalRequirement]:
        reqs = self.goal_requirements.get(goal_id)
        if reqs:
            return reqs
        try:
            from app.personas.registry import persona_registry
            pkg = persona_registry.for_goal(goal_id)
            if pkg:
                return [GoalRequirement(goal_id=goal_id, skill_id=r["skill_id"], required_level=float(r["required_level"]),
                                        importance=float(r.get("importance", 1.0)), source_id="PERSONA") for r in pkg.requirements]
        except Exception:
            pass
        return []

    # ------------------------------------------------------------------ diff + explanation
    def _compute_plan_diff(self, old_plan: Optional[Plan], new_plan: Plan, trigger: Optional[str] = None,
                           reasons: Optional[List[str]] = None) -> PlanDiff:
        if not old_plan:
            return PlanDiff(
                previous_plan_id="NONE", new_plan_id=new_plan.plan_id, added_items=new_plan.items, removed_items=[],
                modified_items=[], trigger=trigger or "initial", reasons=list(reasons or []),
                summary="Initial study plan generated based on diagnostic assessment and curriculum prerequisite analysis.")

        old_map = {item_key(it): it for it in old_plan.items}
        new_map = {item_key(it): it for it in new_plan.items}
        added = [it for k, it in new_map.items() if k not in old_map]
        removed = [it for k, it in old_map.items() if k not in new_map]
        modified = []
        for k, new_it in new_map.items():
            old_it = old_map.get(k)
            if not old_it:
                continue
            changes = {}
            if (old_it.semester_number or 0) != (new_it.semester_number or 0):
                changes["semester"] = [old_it.semester_number, new_it.semester_number]
            if old_it.phase != new_it.phase:
                changes["phase"] = [old_it.phase, new_it.phase]
            if abs((old_it.prep_hours_weekly or 0.0) - (new_it.prep_hours_weekly or 0.0)) >= 0.1:
                changes["weekly_hours"] = [old_it.prep_hours_weekly, new_it.prep_hours_weekly]
            if (old_it.planning_status or "") != (new_it.planning_status or ""):
                changes["status"] = [old_it.planning_status, new_it.planning_status]
            if changes:
                modified.append({"item_type": new_it.item_type, "course_id": new_it.course_id, "label": item_label(new_it), "changes": changes,
                                 "old_phase": old_it.phase, "new_phase": new_it.phase,
                                 "old_hours": old_it.prep_hours_weekly, "new_hours": new_it.prep_hours_weekly})

        parts = []
        if added:
            parts.append(f"Added {len(added)} learning item(s): " + ", ".join(item_label(it) for it in added[:6]) + (" ..." if len(added) > 6 else ""))
        if removed:
            parts.append(f"Removed/Satisfied {len(removed)} item(s): " + ", ".join(item_label(it) for it in removed[:6]) + (" ..." if len(removed) > 6 else ""))
        if modified:
            parts.append(f"Pacing updated for {len(modified)} item(s)")
        summary = "; ".join(parts) if parts else "Plan validated and refreshed with identical curriculum items."
        return PlanDiff(previous_plan_id=old_plan.plan_id, new_plan_id=new_plan.plan_id, added_items=added, removed_items=removed,
                        modified_items=modified, summary=summary, trigger=trigger, reasons=list(reasons or []))

    def _snapshot(self, student_id: str) -> Dict[str, Any]:
        st = onboarding_service.students[student_id]
        goal = onboarding_service.goals.get(student_id)
        cons = self.planner.parse_constraints(onboarding_service.constraints.get(student_id, []))
        states = diagnostic_service.skill_states.get(student_id, [])
        return {
            "goal_id": goal.goal_id if goal else None, "goal_name": goal.name if goal else None,
            "cgpa": st.cgpa, "backlogs": st.backlogs, "current_semester": st.current_semester,
            "credit_cap": cons["credit_cap"], "weekly_hours": cons["weekly_hours"], "avoid": sorted(cons["avoid"]),
            "completed": sorted(onboarding_service.completed_courses.get(student_id, [])),
            "skills": {s.skill_id: s.estimated_level for s in states},
            "evidence_count": len(diagnostic_service.evidence_ledger.get(student_id, [])),
            "minor_eligible": self.planner.rule_engine.check_minor_eligibility(st),
        }

    def _explain_input_changes(self, old: Optional[Dict[str, Any]], new: Dict[str, Any]) -> List[str]:
        """Deterministic 'why' derived from what actually changed in the inputs."""
        if not old:
            return []
        out = []
        if old["goal_id"] != new["goal_id"]:
            out.append(f"Goal changed from {old['goal_name'] or old['goal_id']} to {new['goal_name'] or new['goal_id']}: electives and goal "
                       f"preparation were re-ranked for the new goal; completed courses and all evidence were kept.")
        if old["cgpa"] != new["cgpa"]:
            msg = f"CGPA changed from {old['cgpa']} to {new['cgpa']}."
            if old["minor_eligible"] != new["minor_eligible"]:
                cut = self.planner.rule_engine.minor_cutoff()
                msg += (f" Minor eligibility is now {'met' if new['minor_eligible'] else 'not met'} (cutoff {cut:.2f}, "
                        f"RULE_MINOR_ELIGIBILITY, unsourced baseline).")
            out.append(msg)
        if old["backlogs"] != new["backlogs"]:
            out.append(f"Active backlogs changed from {old['backlogs']} to {new['backlogs']}: backlog clearance is always scheduled before electives.")
        if old["current_semester"] != new["current_semester"]:
            out.append(f"Current semester changed from {old['current_semester']} to {new['current_semester']}: the planning horizon was rebuilt.")
        if old["credit_cap"] != new["credit_cap"]:
            out.append(f"Your credit limit changed from {old['credit_cap']} to {new['credit_cap']} (hard constraint).")
        if old["weekly_hours"] != new["weekly_hours"]:
            out.append(f"Your weekly-hours cap changed from {old['weekly_hours']} to {new['weekly_hours']} h (hard constraint): weekly hours were re-budgeted.")
        newly_avoided = sorted(set(new["avoid"]) - set(old["avoid"]))
        if newly_avoided:
            out.append(f"You rejected {', '.join(newly_avoided)}: it is excluded and the next-best option of the same slot was selected.")
        if old["completed"] != new["completed"]:
            out.append("Your transcript changed: completed courses are never re-assigned and their dependents are unlocked.")
        for sid in sorted(set(old["skills"]) | set(new["skills"])):
            a, b = old["skills"].get(sid), new["skills"].get(sid)
            if a is None and b is not None:
                out.append(f"New assessed evidence for {sid}: level {b:.1f}.")
            elif a is not None and b is not None and abs(a - b) >= 1.0:
                out.append(f"Evidence-weighted level for {sid} moved from {a:.1f} to {b:.1f}.")
        return out

    def _generate_explanation(self, old_plan: Optional[Plan], new_plan: Plan, diff: PlanDiff, mismatch: Optional[Dict[str, Any]]) -> str:
        if not old_plan:
            base = (f"Generated Version 1 of your roadmap for {new_plan.goal_id}. "
                    f"Curriculum sequencing strictly respects institutional prerequisite trees and regular credit caps. ")
            if mismatch and mismatch.get("mismatch_detected"):
                base += f" Note: {mismatch['explanation']}"
            return base
        lines = [f"**Plan Version Adaptation (v{old_plan.version} -> v{new_plan.version}):**",
                 f"- **What Changed:** {diff.summary}"]
        if diff.reasons:
            lines.append("- **Why:** " + " ".join(diff.reasons))
        elif mismatch and mismatch.get("mismatch_detected"):
            lines.append(f"- **Why:** {mismatch['explanation']}")
        else:
            lines.append("- **Why:** Re-planned deterministically from the current evidence ledger, constraints and curriculum rules; "
                         "no input that affects the plan has changed.")
        return "\n".join(lines)

    # ------------------------------------------------------------------ build
    def create_or_update_plan(self, student_id: str, trigger: str = "manual_regen", reasons: Optional[List[str]] = None,
                              horizon: str = "degree") -> Dict[str, Any]:
        student = onboarding_service.students.get(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not onboarded")
        goal = onboarding_service.goals.get(student_id)
        completed = onboarding_service.completed_courses.get(student_id, [])
        constraints = onboarding_service.constraints.get(student_id, [])
        preferences = onboarding_service.preferences.get(student_id, [])
        interests = onboarding_service.interests.get(student_id, [])
        evidence = diagnostic_service.evidence_ledger.get(student_id, [])
        states = diagnostic_service.skill_states.get(student_id, [])

        old_plan = self.plans.get(student_id)
        new_version = (old_plan.version + 1) if old_plan else 1
        reqs = self.requirements_for(goal.goal_id)
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, states, evidence=evidence)

        candidate = self.agent_1.build_roadmap(
            student=student, goal=goal, gaps=gaps, constraints=constraints, preferences=preferences,
            completed_course_ids=completed, skill_states=states,
            aims_text=onboarding_service.aims_and_aspirations.get(student_id) or student.aims,
            version=new_version, horizon=horizon, evidence=evidence, interests=interests)

        new_snap = self._snapshot(student_id)
        auto_reasons = self._explain_input_changes(self.input_snapshots.get(student_id), new_snap)
        all_reasons = list(dict.fromkeys(list(reasons or []) + auto_reasons))
        diff = self._compute_plan_diff(old_plan, candidate, trigger=trigger, reasons=all_reasons)
        what_changed = self._generate_explanation(old_plan, candidate, diff, candidate.mismatch_warning)
        report = self.validator.validate_plan(candidate, student, completed_course_ids=completed, constraints=constraints)

        final_plan = candidate.model_copy(update={"validation_report": report, "plan_diff": diff, "what_changed_and_why": what_changed})
        return self.commit(student_id, final_plan, trigger, gaps=gaps, snapshot=new_snap)

    def commit(self, student_id: str, final_plan: Plan, trigger: str, gaps: Optional[List[Dict[str, Any]]] = None,
               snapshot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Stores a validated plan version (memory + best-effort PostgreSQL) and logs it."""
        old_plan = self.plans.get(student_id)
        if old_plan:
            self.plan_history.setdefault(student_id, []).append(old_plan)
        self.plans[student_id] = final_plan
        if snapshot is not None:
            self.input_snapshots[student_id] = snapshot
        diff = final_plan.plan_diff
        credits = round(sum((it.credits or 0.0) for it in final_plan.items if it.item_type == "course"), 1)
        self.version_log.setdefault(student_id, []).append({
            "version": final_plan.version, "plan_id": final_plan.plan_id, "trigger": trigger,
            "summary": diff.summary if diff else "", "reasons": list(diff.reasons) if diff else [],
            "validation_passed": bool(final_plan.validation_report.passed) if final_plan.validation_report else None,
            "total_items": len(final_plan.items), "total_credits": credits,
            "created_at": final_plan.created_at.isoformat(), "committed_by": "agent_1_planner",
        })
        diff_small = None
        if diff:
            diff_small = {"summary": diff.summary, "trigger": diff.trigger, "reasons": diff.reasons,
                          "added": [item_label(i) for i in diff.added_items], "removed": [item_label(i) for i in diff.removed_items],
                          "modified": diff.modified_items}
        persistence.persist_plan(final_plan.model_dump(mode="json"), trigger, final_plan.what_changed_and_why or "",
                                 diff_small, old_plan.plan_id if old_plan else None)
        report = final_plan.validation_report
        return {
            "plan": final_plan.model_dump(),
            "version": final_plan.version,
            "plan_diff": diff.model_dump() if diff else None,
            "what_changed_and_why": final_plan.what_changed_and_why,
            "mismatch_warning": final_plan.mismatch_warning,
            "gaps": gaps or [],
            "validation": report.model_dump() if report else {"passed": True, "checks": [], "messages": []},
        }

    def goal_repo_has(self, goal_id: str) -> bool:
        return onboarding_service.goal_repo.get_by_id(goal_id) is not None

    def get_plan(self, student_id: str) -> Optional[Plan]:
        return self.plans.get(student_id)

    def get_plan_history(self, student_id: str) -> List[Plan]:
        return self.plan_history.get(student_id, [])

    def get_or_create(self, student_id: str) -> Plan:
        plan = self.plans.get(student_id)
        if plan is None:
            onboarding_service.ensure_student_onboarded(student_id)
            self.create_or_update_plan(student_id, trigger="initial")
            plan = self.plans[student_id]
        return plan

plan_service = PlanService()
