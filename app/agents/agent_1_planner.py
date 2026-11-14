import uuid
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone

from app.contracts.student import StudentProfile, Constraint, Preference, SkillState
from app.contracts.goal import Goal
from app.contracts.plan import Plan, PlanItem, StructuredReason, PlanDiff, ValidationReport
from app.contracts.proposal import ChangeProposal
from app.contracts.roadmap import WeeklyRoadmap, DailyTask, RoadmapVersionRecord
from app.engine.planner import Planner
from app.engine.validator import PlanValidator
from app.engine.rules import RuleEngine
from app.kb.repositories import ResourceRepo, CourseRepo

class RoadmapPlannerAgent:
    """
    AGENT 1 — ROADMAP PLANNER (Sole Designated Writer)
    
    Responsibilities:
    1. Creates the Long-Term Semestral Academic Roadmap.
    2. Breaks down the active semester into structured Weekly Roadmaps with daily tasks.
    3. SOLE WRITER: The only agent with authority to commit/write Roadmap versions.
    4. Validates approved ChangeProposals deterministically and writes Version N+1.
    """
    def __init__(self, seed_dir: str = "data/seed/kb"):
        self.seed_dir = seed_dir
        self.planner_engine = Planner(seed_dir)
        self.validator_engine = PlanValidator(seed_dir)
        self.rule_engine = RuleEngine(seed_dir)
        self.resource_repo = ResourceRepo(seed_dir)
        self.course_repo = CourseRepo(seed_dir)

    def create_initial_roadmap(
        self,
        student: StudentProfile,
        goal: Goal,
        gaps: List[Dict[str, Any]],
        constraints: List[Constraint],
        preferences: List[Preference],
        completed_course_ids: Optional[List[str]] = None
    ) -> Plan:
        """Generates Version 1 of the student's complete academic plan."""
        base_plan = self.planner_engine.generate_plan(
            student=student,
            goal=goal,
            gaps=gaps,
            constraints=constraints,
            preferences=preferences,
            completed_course_ids=completed_course_ids
        )
        report = self.validator_engine.validate_plan(base_plan, student, completed_course_ids)
        validated_plan = base_plan.model_copy(update={
            "version": 1,
            "validation_report": report
        })
        return validated_plan

    def generate_weekly_roadmap(
        self,
        plan: Plan,
        semester_number: int,
        week_number: int,
        daily_hours: float = 2.0
    ) -> WeeklyRoadmap:
        """
        Generates a 7-day weekly study schedule for the given week of the semester,
        grounded in the active courses and curated knowledge-base resources.
        """
        semester_courses = [it for it in plan.items if it.item_type == "course" and it.semester_number == semester_number]
        focus_skills = []
        target_course_ids = []
        for c in semester_courses:
            if c.course_id:
                target_course_ids.append(c.course_id)
                focus_skills.extend(c.reason.target_skills)

        # Unique skills (up to 3 for focus)
        focus_skills = list(dict.fromkeys(focus_skills))[:3]
        target_course_ids = list(dict.fromkeys(target_course_ids))

        # Generate 7 daily tasks
        daily_tasks: List[DailyTask] = []
        days_label = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        # Map available resources from KB for these courses
        all_resources = self.resource_repo.list_all()

        for day_idx in range(1, 8):
            cid = target_course_ids[(day_idx - 1) % len(target_course_ids)] if target_course_ids else "CORE_STUDY"
            course_obj = self.course_repo.get_by_id(cid)
            course_title = course_obj.title if course_obj else cid
            skill_target = focus_skills[(day_idx - 1) % len(focus_skills)] if focus_skills else "CORE_COMPETENCY"

            # Match KB resource if available (primary from resource_course mapping, else search)
            primary_res = self.resource_repo.get_primary_resource_for_course(cid)
            matching_res = primary_res or next((r for r in all_resources if cid in r.title or skill_target.lower() in r.title.lower()), None)

            if day_idx in [1, 2, 4]:
                task = DailyTask(
                    task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                    day_number=day_idx,
                    title=f"{days_label[day_idx-1]}: Lecture & Theory — {course_title}",
                    estimated_minutes=int(daily_hours * 60 * 0.6),
                    task_type="video_lecture",
                    skill_id=skill_target,
                    course_id=cid,
                    resource_id=matching_res.resource_id if matching_res else None,
                    resource_title=matching_res.title if matching_res else f"Curated Lecture Module: {course_title}",
                    resource_url=matching_res.url if matching_res else None
                )
            elif day_idx in [3, 5]:
                task = DailyTask(
                    task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                    day_number=day_idx,
                    title=f"{days_label[day_idx-1]}: Practice Problems & Derivations — {course_title}",
                    estimated_minutes=int(daily_hours * 60 * 0.5),
                    task_type="practice_exercise",
                    skill_id=skill_target,
                    course_id=cid,
                    exercise_id=f"EX_{skill_target}_{week_number}_{day_idx}"
                )
            elif day_idx == 6:
                task = DailyTask(
                    task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                    day_number=day_idx,
                    title=f"{days_label[day_idx-1]}: Weekly Checkpoint Quiz & Review",
                    estimated_minutes=int(daily_hours * 60 * 0.4),
                    task_type="quiz",
                    skill_id=skill_target,
                    course_id=cid
                )
            else: # Sunday
                task = DailyTask(
                    task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                    day_number=day_idx,
                    title=f"{days_label[day_idx-1]}: Rest / Buffer / Project Catch-up",
                    estimated_minutes=int(daily_hours * 60 * 0.3),
                    task_type="revision",
                    skill_id=skill_target,
                    course_id=cid
                )
            daily_tasks.append(task)

        total_hours = sum(t.estimated_minutes for t in daily_tasks) / 60.0

        return WeeklyRoadmap(
            week_number=week_number,
            semester_number=semester_number,
            weekly_objective=f"Master foundational concepts and active problem solving in {', '.join(target_course_ids[:2])}",
            focus_skills=focus_skills,
            target_courses=target_course_ids,
            daily_tasks=daily_tasks,
            milestone_checkpoint=f"Week {week_number} Mastery Evaluation" if week_number % 4 == 0 else None,
            total_estimated_hours=round(total_hours, 1)
        )

    def commit_approved_proposal(
        self,
        current_plan: Plan,
        student: StudentProfile,
        proposal: ChangeProposal,
        completed_course_ids: Optional[List[str]] = None
    ) -> Plan:
        """
        Executes the Single-Writer commit rule:
        1. Validates the proposal against deterministic academic rules.
        2. Produces the new Plan version (N+1).
        3. Attaches the validation report and audit diff.
        """
        if proposal.status != "approved":
            raise ValueError(f"Cannot commit proposal {proposal.proposal_id}: status is '{proposal.status}' (must be 'approved').")

        old_items = current_plan.items
        new_items: List[PlanItem] = []
        
        mods = proposal.proposed_modifications
        add_courses = mods.get("add_courses", [])
        remove_courses = mods.get("remove_courses", [])
        add_exercises = mods.get("add_exercises", [])

        # Filter out removed courses
        for it in old_items:
            if it.course_id and it.course_id in remove_courses:
                continue
            new_items.append(it)

        # Add newly scheduled courses
        for cid in add_courses:
            c_meta = self.course_repo.get_by_id(cid)
            c_title = c_meta.title if c_meta else cid
            new_items.append(PlanItem(
                item_id=f"ITEM_C_{cid}_{uuid.uuid4().hex[:6]}",
                item_type="course",
                course_id=cid,
                semester_number=proposal.target_semester or student.current_semester,
                estimated_hours=4.0,
                reason=StructuredReason(
                    intent="Adaptive Schedule Modification",
                    target_skills=[],
                    why_this=f"Scheduled per approved proposal {proposal.proposal_id}: {proposal.reasoning}",
                    prerequisite_for=[],
                    rule_compliance=["Validated under academic offering guidelines"]
                )
            ))

        # Add remediation / practice items
        for ex_info in add_exercises:
            new_items.append(PlanItem(
                item_id=f"ITEM_REM_{uuid.uuid4().hex[:6]}",
                item_type="remediation",
                course_id=ex_info.get("course_id"),
                exercise_id=ex_info.get("exercise_id"),
                semester_number=proposal.target_semester or student.current_semester,
                scheduled_week=proposal.target_week,
                estimated_hours=float(ex_info.get("hours", 2.0)),
                reason=StructuredReason(
                    intent="Mastery Remediation",
                    target_skills=[ex_info.get("skill_id", "REMEDIATION")],
                    why_this=proposal.reasoning,
                    prerequisite_for=[],
                    rule_compliance=[]
                )
            ))

        candidate_plan = Plan(
            plan_id=f"PLAN_{student.student_id}_{uuid.uuid4().hex[:8]}",
            student_id=student.student_id,
            goal_id=current_plan.goal_id,
            version=current_plan.version + 1,
            items=new_items,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )

        # Strict deterministic validation check
        report = self.validator_engine.validate_plan(candidate_plan, student, completed_course_ids)
        if not report.passed:
            updated_prop = proposal.model_copy(update={"status": "validation_failed", "resolved_at": datetime.now(timezone.utc)})
            raise ValueError(f"Plan validation failed for proposal {proposal.proposal_id}: {'; '.join(report.messages)}")

        final_plan = candidate_plan.model_copy(update={"validation_report": report})
        updated_prop = proposal.model_copy(update={"status": "committed", "resolved_at": datetime.now(timezone.utc)})

        return final_plan, updated_prop
