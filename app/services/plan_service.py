import os
import csv
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.contracts.student import StudentProfile
from app.contracts.goal import Goal, GoalRequirement
from app.contracts.plan import Plan, PlanItem, PlanDiff, ValidationReport
from app.engine.planner import Planner
from app.engine.validator import PlanValidator
from app.engine.gaps import GapAnalyzer
from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service

class PlanService:
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self.planner = Planner(seed_dir)
        self.validator = PlanValidator(seed_dir)
        self.gap_analyzer = GapAnalyzer()
        self.plans: Dict[str, Plan] = {}
        self.plan_history: Dict[str, List[Plan]] = {}
        self.goal_requirements: Dict[str, List[GoalRequirement]] = {}
        self._load_requirements()

    def _load_requirements(self):
        path = os.path.join(self.seed_dir, "goal_skill_requirement.csv")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    gid = r["goal_id"]
                    self.goal_requirements.setdefault(gid, []).append(GoalRequirement(
                        goal_id=gid,
                        skill_id=r["skill_id"],
                        required_level=float(r["required_level"]),
                        importance=float(r.get("importance", 1.0)),
                        source_id=r.get("source_id", "DESIGN_TEAM")
                    ))

    def _compute_plan_diff(self, old_plan: Optional[Plan], new_plan: Plan) -> PlanDiff:
        if not old_plan:
            return PlanDiff(
                previous_plan_id="NONE",
                new_plan_id=new_plan.plan_id,
                added_items=new_plan.items,
                removed_items=[],
                modified_items=[],
                summary="Initial study plan generated based on diagnostic assessment and curriculum prerequisite analysis."
            )

        old_cids = {it.course_id: it for it in old_plan.items if it.course_id}
        new_cids = {it.course_id: it for it in new_plan.items if it.course_id}

        added = [it for it in new_plan.items if it.course_id and it.course_id not in old_cids]
        removed = [it for it in old_plan.items if it.course_id and it.course_id not in new_cids]

        modified = []
        for cid, new_it in new_cids.items():
            if cid in old_cids:
                old_it = old_cids[cid]
                if old_it.phase != new_it.phase or old_it.prep_hours_weekly != new_it.prep_hours_weekly:
                    modified.append({
                        "course_id": cid,
                        "old_phase": old_it.phase,
                        "new_phase": new_it.phase,
                        "old_hours": old_it.prep_hours_weekly,
                        "new_hours": new_it.prep_hours_weekly
                    })

        changes_desc = []
        if added:
            cids_str = ", ".join(it.course_id for it in added if it.course_id)
            changes_desc.append(f"Added {len(added)} learning item(s): {cids_str}")
        if removed:
            cids_str = ", ".join(it.course_id for it in removed if it.course_id)
            changes_desc.append(f"Removed/Satisfied {len(removed)} item(s): {cids_str}")
        if modified:
            changes_desc.append(f"Pacing updated for {len(modified)} item(s)")

        summary = "; ".join(changes_desc) if changes_desc else "Plan validated and refreshed with identical curriculum items."

        return PlanDiff(
            previous_plan_id=old_plan.plan_id,
            new_plan_id=new_plan.plan_id,
            added_items=added,
            removed_items=removed,
            modified_items=modified,
            summary=summary
        )

    def _generate_explanation(self, old_plan: Optional[Plan], new_plan: Plan, diff: PlanDiff, mismatch: Optional[Dict[str, Any]]) -> str:
        if not old_plan:
            base_exp = (
                f"Generated Version 1 of your semester roadmap for {new_plan.goal_id}. "
                f"Curriculum sequencing strictly respects institutional prerequisite trees and regular credit caps. "
            )
            if mismatch and mismatch.get("mismatch_detected"):
                base_exp += f" Note: {mismatch['explanation']}"
            return base_exp

        reasons = [
            f"**Plan Version Adaptation (v{old_plan.version} -> v{new_plan.version}):**",
            f"- **What Changed:** {diff.summary}"
        ]

        if mismatch and mismatch.get("mismatch_detected"):
            reasons.append(f"- **Why:** {mismatch['explanation']}")
        else:
            reasons.append(
                f"- **Why:** Adapted study sequence in response to updated objective evidence, quiz performances, "
                f"and academic calendar load adjustments to safeguard your CGPA and ensure readiness."
            )

        return "\n".join(reasons)

    def create_or_update_plan(self, student_id: str) -> Dict[str, Any]:
        student = onboarding_service.students.get(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not onboarded")

        goal = onboarding_service.goals.get(student_id)
        completed = onboarding_service.completed_courses.get(student_id, [])
        constraints = onboarding_service.constraints.get(student_id, [])
        preferences = onboarding_service.preferences.get(student_id, [])
        states = diagnostic_service.skill_states.get(student_id, [])

        old_plan = self.plans.get(student_id)
        new_version = (old_plan.version + 1) if old_plan else 1

        reqs = self.goal_requirements.get(goal.goal_id, [])
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, states)

        # Generate candidate plan with adaptive phase weeks and mismatch detection
        candidate_plan = self.planner.generate_plan(
            student=student,
            goal=goal,
            gaps=gaps,
            constraints=constraints,
            preferences=preferences,
            completed_course_ids=completed,
            skill_states=states,
            aims_text=getattr(student, "aims_and_aspirations", None),
            version=new_version
        )

        # Compute diff and "What changed and why"
        diff = self._compute_plan_diff(old_plan, candidate_plan)
        what_changed = self._generate_explanation(old_plan, candidate_plan, diff, candidate_plan.mismatch_warning)

        # Validate with deterministic validator
        report = self.validator.validate_plan(candidate_plan, student, completed_course_ids=completed)
        
        final_plan = candidate_plan.model_copy(update={
            "validation_report": report,
            "plan_diff": diff,
            "what_changed_and_why": what_changed
        })

        if old_plan:
            self.plan_history.setdefault(student_id, []).append(old_plan)
        self.plans[student_id] = final_plan

        return {
            "plan": final_plan.model_dump(),
            "version": final_plan.version,
            "plan_diff": diff.model_dump(),
            "what_changed_and_why": what_changed,
            "mismatch_warning": final_plan.mismatch_warning,
            "gaps": gaps,
            "validation": report.model_dump()
        }

    def get_plan(self, student_id: str) -> Optional[Plan]:
        return self.plans.get(student_id)

    def get_plan_history(self, student_id: str) -> List[Plan]:
        return self.plan_history.get(student_id, [])

plan_service = PlanService()
