import os
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.contracts.student import StudentProfile, EvidenceItem, SkillState, Constraint, Preference
from app.contracts.goal import Goal
from app.contracts.plan import Plan, PlanDiff
from app.contracts.proposal import ChangeProposal
from app.contracts.roadmap import WeeklyRoadmap, RoadmapVersionRecord
from app.contracts.kb import Exercise
from app.contracts.chat import ContextCard

from app.agents.agent_1_planner import RoadmapPlannerAgent
from app.agents.agent_2_learning import LearningResourceAgent
from app.agents.agent_3_assessment import AssessmentMasteryAgent
from app.agents.agent_4_query import QueryAdaptationAgent

from app.services.onboarding_service import onboarding_service
from app.services.diagnostic_service import diagnostic_service
from app.services.plan_service import plan_service
from app.db import persistence

logger = logging.getLogger("ebuddy.orchestrator")

class RoadmapOrchestrator:
    """
    Central Orchestrator enforcing the Four-Agent System and Single-Writer Rule:
    
    Workflow:
      Agent 2 / 3 / 4 -> ChangeProposal
          ↓
      Student Reviews Proposal
          ↓
      Student Approves?
        /          \
     NO             YES
      ↓              ↓
    REJECTED    Deterministic Validation (PlanValidator)
    Roadmap          ↓
    Unchanged   Agent 1 (Sole Writer) Commits Version N+1
    """
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self.agent_1 = plan_service.agent_1  # shared instance: ONE writer, one KB view
        self.agent_2 = LearningResourceAgent(seed_dir)
        self.agent_3 = AssessmentMasteryAgent()
        self.agent_4 = QueryAdaptationAgent()

        # In-memory shared state stores
        self.proposals: Dict[str, ChangeProposal] = {}
        self.student_proposals: Dict[str, List[str]] = {} # student_id -> [proposal_id]
        self.version_history: Dict[str, List[RoadmapVersionRecord]] = {} # student_id -> [records]
        self.weekly_roadmaps: Dict[str, WeeklyRoadmap] = {} # student_id -> active weekly roadmap
        self.memory_summaries: Dict[str, str] = {} # student_id -> rolling conversation summary

    def _load_memory_summary(self, student_id: str) -> Optional[str]:
        return persistence.load_memory_summary(student_id) or self.memory_summaries.get(student_id)

    def _save_memory_summary(self, student_id: str, summary_text: str):
        self.memory_summaries[student_id] = summary_text
        persistence.save_memory_summary(student_id, summary_text)

    def _persist_proposal_to_db(self, proposal: ChangeProposal):
        """Mirrors a change proposal to plan.change_proposal (best effort)."""
        persistence.persist_proposal(proposal.model_dump(mode="json"))

    def reset(self):
        self.proposals.clear(); self.student_proposals.clear(); self.version_history.clear()
        self.weekly_roadmaps.clear(); self.memory_summaries.clear()

    def _record_version(self, student_id: str, plan: Plan, reason: str, proposal_id: Optional[str], diff_summary: str):
        rec = RoadmapVersionRecord(
            version_id=f"VER_{student_id}_{plan.version}_{uuid.uuid4().hex[:6]}", plan_id=plan.plan_id, student_id=student_id,
            version_number=plan.version, commit_reason=reason, approved_proposal_id=proposal_id, total_items=len(plan.items),
            total_credits=sum((it.credits or 0.0) for it in plan.items if it.item_type == "course"),
            diff_summary=diff_summary, committed_at=datetime.now(timezone.utc))
        self.version_history.setdefault(student_id, []).append(rec)
        return rec

    def create_initial_roadmap(self, student_id: str) -> Dict[str, Any]:
        """Agent 1 builds the roadmap (all remaining semesters); the plan service validates, diffs and stores it."""
        student = onboarding_service.students.get(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not onboarded")
        res = plan_service.create_or_update_plan(student_id, trigger="initial" if not plan_service.get_plan(student_id) else "manual_regen")
        plan = plan_service.get_plan(student_id)
        weekly = self.get_weekly_roadmap(student_id, week_number=1)
        self._record_version(student_id, plan, "Roadmap built by Agent 1 (Roadmap Planner)", None,
                             plan.plan_diff.summary if plan.plan_diff else "Baseline roadmap")
        return {
            "plan": res["plan"],
            "weekly_roadmap": weekly.model_dump(),
            "version": plan.version,
            "validation": res["validation"],
        }

    def get_weekly_roadmap(self, student_id: str, week_number: int = 1) -> WeeklyRoadmap:
        """Retrieves or generates the weekly roadmap for the student, enforcing weekly hours budget if set."""
        current_plan = plan_service.get_or_create(student_id)
        student = onboarding_service.students.get(student_id)
        sem = student.current_semester if student else 1

        budget = plan_service.planner.parse_constraints(onboarding_service.constraints.get(student_id, []))["weekly_hours"]

        weekly = self.agent_1.generate_weekly_roadmap(current_plan, semester_number=sem, week_number=week_number, weekly_hours_budget=budget)
        self.weekly_roadmaps[student_id] = weekly
        return weekly

    def get_today_learning(self, student_id: str) -> Dict[str, Any]:
        """Invokes Agent 2 to recommend today's verified resources from the KB."""
        current_plan = plan_service.get_or_create(student_id)

        states = {s.skill_id: s for s in diagnostic_service.skill_states.get(student_id, [])}
        prefs = onboarding_service.preferences.get(student_id, [])
        return self.agent_2.get_daily_recommendations(current_plan, current_week=1, student_skill_states=states, preferences=prefs)

    def submit_assessment(self, student_id: str, exercise: Exercise, student_answer: str) -> Dict[str, Any]:
        """
        Invokes Agent 3 to evaluate the student's submission.
        Strict Single-Writer Rule: If performance is poor, Agent 3 emits an AdaptationProposal.
        The roadmap is NOT changed until the student reviews and approves it.
        """
        existing_ev = diagnostic_service.evidence_ledger.get(student_id, [])
        eval_result = self.agent_3.evaluate_submission(student_id, exercise, student_answer, existing_ev)

        # Update evidence and states
        # An objectively graded item is assessed (strong) evidence
        new_ev = eval_result["new_evidence_item"]
        if exercise.exercise_type in ("mcq", "numeric"):
            new_ev = new_ev.model_copy(update={"source_type": "diagnostic", "notes": f"Adaptive item {exercise.exercise_id}"})
        diagnostic_service.evidence_ledger.setdefault(student_id, []).append(new_ev)
        diagnostic_service.skill_states[student_id] = diagnostic_service.state_updater.update_states(
            student_id, diagnostic_service.evidence_ledger[student_id])

        proposal: Optional[ChangeProposal] = None
        # Insufficient mastery trigger -> Propose remediation
        if eval_result["score"] < 75.0:
            proposal = self.agent_3.propose_remediation(
                student_id=student_id,
                skill_id=exercise.skill_id,
                score=eval_result["score"],
                target_week=1,
                course_id=None
            )
            self.proposals[proposal.proposal_id] = proposal
            self.student_proposals.setdefault(student_id, []).append(proposal.proposal_id)
            self._persist_proposal_to_db(proposal)

        return {
            "exercise_id": exercise.exercise_id,
            "score": eval_result["score"],
            "is_correct": eval_result["is_correct"],
            "feedback": eval_result["feedback"],
            "demonstrated_mastery": eval_result["demonstrated_mastery"],
            "proposal": proposal.model_dump() if proposal else None
        }

    def chat_turn(self, student_id: str, message: str) -> Dict[str, Any]:
        """
        Invokes Agent 4 for conversational guidance.
        Loads rolling conversation memory from ops.memory_summary into ContextCard,
        and saves updated rolling summary for long-term multi-session retention.
        """
        # Load the real profile (seed / database) instead of answering from placeholder defaults;
        # an unknown id raises StudentNotFoundError (404 at the API).
        onboarding_service.ensure_student_onboarded(student_id)
        student = onboarding_service.students.get(student_id)
        goal = onboarding_service.goals.get(student_id)
        plan = plan_service.get_plan(student_id)
        states = diagnostic_service.skill_states.get(student_id, [])

        plan_items = [it.model_dump() for it in plan.items] if plan else []
        skill_gaps = [{"skill_id": s.skill_id, "estimated_level": s.estimated_level} for s in states]

        memory = self._load_memory_summary(student_id)

        card = ContextCard(
            student_id=student_id,
            programme_id=student.programme_id if student else "BTECH_EE",
            current_semester=student.current_semester if student else 1,
            cgpa=student.cgpa if student else 8.0,
            goal_id=goal.goal_id if goal else "GOAL_EE_CORE_POWER",
            goal_name=goal.name if goal else "Electrical Engineering Core",
            skill_gaps=skill_gaps,
            current_plan_items=plan_items,
            long_term_memory=memory,
            verified_facts=[
                {"fact": "Programme Curriculum", "value": "B.Tech Curriculum 2016-17", "verified": True},
            ],
            unverified_advisories=[
                {"advisory": "Credit Cap Rule", "value": "26 credits per regular semester (unsourced baseline; warning only)", "verified": False},
                {"advisory": "Examination Dates", "value": "Not confirmed yet (contact Academic Section)", "verified": False}
            ]
        )

        res = self.agent_4.handle_query(student_id, message, card)
        if "turn_id" not in res:
            res["turn_id"] = f"TURN_{uuid.uuid4().hex[:8]}"

        # Save rolling conversation summary to ops.memory_summary
        turn_brief = f"Turn: User asked '{message[:40]}' -> Intent: {res.get('inferred_intent', 'general')}. Replied: '{res.get('response', '')[:50]}'."
        updated_memory = f"{memory} | {turn_brief}" if memory else turn_brief
        if len(updated_memory) > 400:
            updated_memory = updated_memory[-400:]
        self._save_memory_summary(student_id, updated_memory)

        raw_prop = res.get("proposal")
        if raw_prop:
            proposal = ChangeProposal.model_validate(raw_prop)
            self.proposals[proposal.proposal_id] = proposal
            self.student_proposals.setdefault(student_id, []).append(proposal.proposal_id)
            self._persist_proposal_to_db(proposal)

        return res

    def list_pending_proposals(self, student_id: str) -> List[ChangeProposal]:
        """Returns all unapproved change proposals for the student."""
        pids = self.student_proposals.get(student_id, [])
        return [self.proposals[p] for p in pids if p in self.proposals and self.proposals[p].status == "pending_student_approval"]

    def decide_proposal(self, student_id: str, proposal_id: str, approve: bool, feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes student decision on a ChangeProposal:
        - If REJECTED: Mark rejected, roadmap is NOT modified.
        - If APPROVED: Invokes Agent 1 to commit the change into Roadmap Version N+1.
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal or proposal.student_id != student_id:
            raise ValueError(f"Proposal {proposal_id} not found for student {student_id}")

        if proposal.status != "pending_student_approval":
            raise ValueError(f"Proposal {proposal_id} is already in state '{proposal.status}'")

        if not approve:
            proposal = proposal.model_copy(update={
                "status": "rejected",
                "student_feedback": feedback,
                "resolved_at": datetime.now(timezone.utc)
            })
            self.proposals[proposal_id] = proposal
            self._persist_proposal_to_db(proposal)
            return {
                "proposal_id": proposal_id,
                "status": "rejected",
                "message": "Proposal rejected. The current roadmap remains unchanged.",
                "roadmap_modified": False
            }

        # Student approved -> Agent 1 commits new version
        approved_prop = proposal.model_copy(update={
            "status": "approved",
            "student_feedback": feedback,
            "resolved_at": datetime.now(timezone.utc)
        })
        self.proposals[proposal_id] = approved_prop

        current_plan = plan_service.get_or_create(student_id)
        student = onboarding_service.students.get(student_id)
        completed = onboarding_service.completed_courses.get(student_id, [])
        constraints = onboarding_service.constraints.get(student_id, [])
        mods = approved_prop.proposed_modifications or {}
        why = [f"You approved a {approved_prop.proposal_type} proposal from {approved_prop.proposer_agent}: {approved_prop.reasoning}"]

        # Proposals that change an INPUT (goal, weekly hours) are applied to the input and the whole
        # roadmap is re-planned deterministically; item-level proposals are committed by Agent 1 directly.
        replanned = False
        if approved_prop.proposal_type == "goal_pivot" and mods.get("target_goal_id"):
            onboarding_service.switch_goal(student_id, mods["target_goal_id"])
            replanned = True
        elif approved_prop.proposal_type == "workload_reduction" and mods.get("weekly_hours_cap"):
            onboarding_service.set_constraint(student_id, "weekly_hours", {"max_hours": float(mods["weekly_hours_cap"])})
            replanned = True

        if replanned:
            plan_service.create_or_update_plan(student_id, trigger=f"proposal:{approved_prop.proposal_type}", reasons=why)
            new_plan = plan_service.get_plan(student_id)
            committed_prop = approved_prop.model_copy(update={"status": "committed", "resolved_at": datetime.now(timezone.utc)})
        else:
            new_plan, committed_prop = self.agent_1.commit_approved_proposal(
                current_plan=current_plan, student=student, proposal=approved_prop, completed_course_ids=completed)
            report = plan_service.validator.validate_plan(new_plan, student, completed_course_ids=completed, constraints=constraints)
            if not report.passed:
                failed = approved_prop.model_copy(update={"status": "validation_failed", "resolved_at": datetime.now(timezone.utc)})
                self.proposals[proposal_id] = failed
                self._persist_proposal_to_db(failed)
                raise ValueError(f"Plan validation failed for proposal {proposal_id}: {'; '.join(report.messages)}")
            diff = plan_service._compute_plan_diff(current_plan, new_plan, trigger=f"proposal:{approved_prop.proposal_type}", reasons=why)
            new_plan = new_plan.model_copy(update={
                "validation_report": report, "plan_diff": diff,
                "what_changed_and_why": plan_service._generate_explanation(current_plan, new_plan, diff, None)})
            plan_service.commit(student_id, new_plan, trigger=f"proposal:{approved_prop.proposal_type}")

        self.proposals[proposal_id] = committed_prop
        updated_weekly = self.get_weekly_roadmap(student_id, week_number=min(16, max(1, committed_prop.target_week or 1)))
        diff_summary = f"Roadmap adapted via {committed_prop.proposer_agent} ({committed_prop.proposal_type}): {committed_prop.impact_summary}"
        self._record_version(student_id, new_plan, committed_prop.reasoning, proposal_id, diff_summary)
        self._persist_proposal_to_db(committed_prop)

        return {
            "proposal_id": proposal_id,
            "status": "committed",
            "message": f"Proposal approved! Agent 1 committed Roadmap Version {new_plan.version}.",
            "roadmap_modified": True,
            "new_version": new_plan.version,
            "diff_summary": diff_summary,
            "plan_diff": new_plan.plan_diff.model_dump() if new_plan.plan_diff else None,
            "new_plan": new_plan.model_dump(),
            "updated_weekly_roadmap": updated_weekly.model_dump()
        }

    def get_version_history(self, student_id: str) -> List[RoadmapVersionRecord]:
        """Returns the version audit history for the student."""
        return self.version_history.get(student_id, [])

roadmap_orchestrator = RoadmapOrchestrator()
