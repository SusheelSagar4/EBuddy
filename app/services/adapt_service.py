import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone
from app.contracts.student import EvidenceItem
from app.contracts.plan import PlanDiff, Plan
from app.engine.skill_state import SkillStateUpdater
from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service
from app.services.plan_service import plan_service
from app.llm.tasks.explainer import Explainer

class AdaptService:
    def __init__(self):
        self.state_updater = SkillStateUpdater()
        self.explainer = Explainer()

    def adapt_to_quiz_score(
        self,
        student_id: str,
        skill_id: str,
        score: float
    ) -> Dict[str, Any]:
        student = onboarding_service.students.get(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not found")

        old_plan = plan_service.get_plan(student_id)
        old_items = old_plan.items if old_plan else []

        # 1. Record quiz score evidence
        ev = EvidenceItem(
            evidence_id=f"EV_QUIZ_{uuid.uuid4().hex[:8]}",
            student_id=student_id,
            skill_id=skill_id,
            source_type="quiz",
            score=score,
            reliability=1.2,
            attempts=1,
            recorded_at=datetime.now(timezone.utc)
        )
        diagnostic_service.evidence_ledger.setdefault(student_id, []).append(ev)

        # 2. Update SkillStates
        updated_states = self.state_updater.update_states(student_id, diagnostic_service.evidence_ledger[student_id])
        diagnostic_service.skill_states[student_id] = updated_states

        # 3. Regenerate Plan
        new_plan_data = plan_service.create_or_update_plan(student_id)
        new_plan = plan_service.get_plan(student_id)
        new_items = new_plan.items if new_plan else []

        # 4. Compute PlanDiff
        old_cids = {it.course_id for it in old_items if it.course_id}
        new_cids = {it.course_id for it in new_items if it.course_id}

        added = [it for it in new_items if it.course_id and it.course_id not in old_cids]
        removed = [it for it in old_items if it.course_id and it.course_id not in new_cids]

        summary = f"Plan adapted after quiz result (Score: {score} on {skill_id}). "
        if score >= 80.0:
            summary += f"Proficiency demonstrated in {skill_id}; advanced content prioritized."
        else:
            summary += f"Remediation and reinforcement scheduled for {skill_id}."

        diff = PlanDiff(
            previous_plan_id=old_plan.plan_id if old_plan else "NONE",
            new_plan_id=new_plan.plan_id,
            added_items=added,
            removed_items=removed,
            modified_items=[],
            summary=summary
        )

        return {
            "score": score,
            "skill_id": skill_id,
            "diff": diff.model_dump(),
            "new_plan": new_plan_data
        }

adapt_service = AdaptService()

