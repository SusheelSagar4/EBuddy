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
        self.agent_1 = RoadmapPlannerAgent(seed_dir)
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
        try:
            import psycopg
            conn = psycopg.connect("postgresql://ebuddy_user:ebuddy_password@127.0.0.1:5432/ebuddy", connect_timeout=1)
            with conn.cursor() as cur:
                cur.execute("SELECT summary_text FROM ops.memory_summary WHERE student_id = %s ORDER BY updated_at DESC LIMIT 1;", (student_id,))
                row = cur.fetchone()
                if row:
                    return row[0]
            conn.close()
        except Exception:
            pass
        return self.memory_summaries.get(student_id)

    def _save_memory_summary(self, student_id: str, summary_text: str):
        self.memory_summaries[student_id] = summary_text
        try:
            import psycopg
            conn = psycopg.connect("postgresql://ebuddy_user:ebuddy_password@127.0.0.1:5432/ebuddy", connect_timeout=1)
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ops.memory_summary (student_id, summary_text) VALUES (%s, %s);",
                    (student_id, summary_text)
                )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _persist_proposal_to_db(self, proposal: ChangeProposal):
        """Optionally persists change proposal to PostgreSQL plan.change_proposal."""
        try:
            import psycopg
            conn = psycopg.connect("postgresql://ebuddy_user:ebuddy_password@127.0.0.1:5432/ebuddy", connect_timeout=1)
            import json
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO plan.change_proposal 
                    (proposal_id, student_id, proposer_agent, proposal_type, status, reasoning, target_week, target_semester, proposed_modifications, impact_summary, student_feedback)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (proposal_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    student_feedback = EXCLUDED.student_feedback,
                    resolved_at = CURRENT_TIMESTAMP
                    """,
                    (
                        proposal.proposal_id,
                        proposal.student_id,
                        proposal.proposer_agent,
                        proposal.proposal_type,
                        proposal.status,
                        proposal.reasoning,
                        proposal.target_week,
                        proposal.target_semester,
                        json.dumps(proposal.proposed_modifications),
                        proposal.impact_summary,
                        proposal.student_feedback
                    )
                )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"Unable to persist proposal to DB: {e}")

    def _persist_version_to_db(self, record: RoadmapVersionRecord, plan: Plan):
        """Persists committed roadmap version record to PostgreSQL plan.roadmap_version."""
        try:
            import psycopg
            conn = psycopg.connect("postgresql://ebuddy_user:ebuddy_password@127.0.0.1:5432/ebuddy", connect_timeout=1)
            import json
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO plan.roadmap_version 
                    (plan_id, student_id, version_number, commit_reason, approved_proposal_id, plan_snapshot, diff_from_previous)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        record.plan_id,
                        record.student_id,
                        record.version_number,
                        record.commit_reason,
                        record.approved_proposal_id,
                        json.dumps(plan.model_dump(), default=str),
                        json.dumps({"summary": record.diff_summary})
                    )
                )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"Unable to persist roadmap version to DB: {e}")

    def create_initial_roadmap(self, student_id: str) -> Dict[str, Any]:
        """Invokes Agent 1 to create the initial Version 1 roadmap."""
        student = onboarding_service.students.get(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not onboarded")

        goal = onboarding_service.goals.get(student_id)
        completed = onboarding_service.completed_courses.get(student_id, [])
        constraints = onboarding_service.constraints.get(student_id, [])
        preferences = onboarding_service.preferences.get(student_id, [])
        states = diagnostic_service.skill_states.get(student_id, [])

        # Calculate gaps
        reqs = plan_service.goal_requirements.get(goal.goal_id, [])
        gaps = plan_service.gap_analyzer.analyze_gaps(goal, reqs, states)

        # Agent 1 produces Plan v1
        v1_plan = self.agent_1.create_initial_roadmap(
            student=student,
            goal=goal,
            gaps=gaps,
            constraints=constraints,
            preferences=preferences,
            completed_course_ids=completed
        )

        plan_service.plans[student_id] = v1_plan

        # Generate initial Week 1 schedule
        weekly = self.agent_1.generate_weekly_roadmap(
            plan=v1_plan,
            semester_number=student.current_semester,
            week_number=1,
            daily_hours=2.0
        )
        self.weekly_roadmaps[student_id] = weekly

        # Record Version 1 in history
        rec = RoadmapVersionRecord(
            version_id=f"VER_{student_id}_1_{uuid.uuid4().hex[:6]}",
            plan_id=v1_plan.plan_id,
            student_id=student_id,
            version_number=1,
            commit_reason="Initial baseline roadmap created by Agent 1 (Roadmap Planner)",
            approved_proposal_id=None,
            total_items=len(v1_plan.items),
            total_credits=sum(self.agent_1.course_repo.get_by_id(it.course_id).credits for it in v1_plan.items if it.course_id and self.agent_1.course_repo.get_by_id(it.course_id)),
            diff_summary="Baseline Roadmap v1 initial commitment.",
            committed_at=datetime.now(timezone.utc)
        )
        self.version_history.setdefault(student_id, []).append(rec)
        self._persist_version_to_db(rec, v1_plan)

        return {
            "plan": v1_plan.model_dump(),
            "weekly_roadmap": weekly.model_dump(),
            "version": 1,
            "validation": v1_plan.validation_report.model_dump() if v1_plan.validation_report else None
        }

    def get_weekly_roadmap(self, student_id: str, week_number: int = 1) -> WeeklyRoadmap:
        """Retrieves or generates the weekly roadmap for the student, enforcing weekly hours budget if set."""
        current_plan = plan_service.get_plan(student_id)
        if not current_plan:
            raise ValueError(f"No active plan found for student {student_id}")

        student = onboarding_service.students.get(student_id)
        sem = student.current_semester if student else 1

        budget = None
        for c in onboarding_service.constraints.get(student_id, []):
            if getattr(c, "is_active", True) and getattr(c, "constraint_type", "") in ["weekly_hours", "max_weekly_hours", "study_hours"]:
                p = getattr(c, "parameters", {})
                budget = float(p.get("max_hours") or p.get("weekly_hours") or p.get("hours") or 0.0)
                break

        weekly = self.agent_1.generate_weekly_roadmap(current_plan, semester_number=sem, week_number=week_number, weekly_hours_budget=budget)
        self.weekly_roadmaps[student_id] = weekly
        return weekly

    def get_today_learning(self, student_id: str) -> Dict[str, Any]:
        """Invokes Agent 2 to recommend today's verified resources from the KB."""
        current_plan = plan_service.get_plan(student_id)
        if not current_plan:
            raise ValueError(f"No active plan found for student {student_id}")

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
        diagnostic_service.evidence_ledger.setdefault(student_id, []).append(eval_result["new_evidence_item"])
        diagnostic_service.skill_states[student_id] = eval_result["updated_states"]

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
                {"fact": "Credit Cap Rule", "value": "Regular Semester Credit Cap: 16-26 credits", "verified": True}
            ],
            unverified_advisories=[
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

        current_plan = plan_service.get_plan(student_id)
        student = onboarding_service.students.get(student_id)
        completed = onboarding_service.completed_courses.get(student_id, [])

        new_plan, committed_prop = self.agent_1.commit_approved_proposal(
            current_plan=current_plan,
            student=student,
            proposal=approved_prop,
            completed_course_ids=completed
        )

        self.proposals[proposal_id] = committed_prop

        # Update canonical plan in plan_service
        plan_service.plans[student_id] = new_plan

        # Regenerate updated weekly schedule
        updated_weekly = self.agent_1.generate_weekly_roadmap(
            plan=new_plan,
            semester_number=student.current_semester,
            week_number=committed_prop.target_week or 1
        )
        self.weekly_roadmaps[student_id] = updated_weekly

        # Record Version Record
        diff_summary = f"Roadmap adapted via {committed_prop.proposer_agent} ({committed_prop.proposal_type}): {committed_prop.impact_summary}"
        ver_record = RoadmapVersionRecord(
            version_id=f"VER_{student_id}_{new_plan.version}_{uuid.uuid4().hex[:6]}",
            plan_id=new_plan.plan_id,
            student_id=student_id,
            version_number=new_plan.version,
            commit_reason=committed_prop.reasoning,
            approved_proposal_id=proposal_id,
            total_items=len(new_plan.items),
            total_credits=sum(self.agent_1.course_repo.get_by_id(it.course_id).credits for it in new_plan.items if it.course_id and self.agent_1.course_repo.get_by_id(it.course_id)),
            diff_summary=diff_summary,
            committed_at=datetime.now(timezone.utc)
        )
        self.version_history.setdefault(student_id, []).append(ver_record)
        self._persist_proposal_to_db(committed_prop)
        self._persist_version_to_db(ver_record, new_plan)

        return {
            "proposal_id": proposal_id,
            "status": "committed",
            "message": f"Proposal approved! Agent 1 committed Roadmap Version {new_plan.version}.",
            "roadmap_modified": True,
            "new_version": new_plan.version,
            "diff_summary": diff_summary,
            "new_plan": new_plan.model_dump(),
            "updated_weekly_roadmap": updated_weekly.model_dump()
        }

    def get_version_history(self, student_id: str) -> List[RoadmapVersionRecord]:
        """Returns the version audit history for the student."""
        return self.version_history.get(student_id, [])

roadmap_orchestrator = RoadmapOrchestrator()
