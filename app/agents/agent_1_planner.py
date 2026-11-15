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
        daily_hours: float = 2.0,
        weekly_hours_budget: Optional[float] = None
    ) -> WeeklyRoadmap:
        """
        Generates a 7-day weekly study schedule for the given week of the semester,
        grounded in the active courses and curated knowledge-base resources.
        If weekly_hours_budget is provided, prunes daily tasks to fit within budget
        and explicitly records deferred tasks.
        """
        # Non-negotiable Rule: Daily tasks must NEVER include REQUIRED_COURSE or enrolled ELECTIVE_PICK
        # lecture items. Daily tasks must consist solely of practice, exercises, revision, and prep
        # items tied directly to the goal skills.
        prep_items = [
            it for it in plan.items 
            if it.item_type not in ["course", "REQUIRED_COURSE", "ELECTIVE_PICK"] 
            and it.semester_number == semester_number
        ]
        
        # Focus skills from prep items and goal requirements
        focus_skills = []
        for it in prep_items:
            if getattr(it, "reason", None) and getattr(it.reason, "target_skills", None):
                focus_skills.extend(it.reason.target_skills)
            elif getattr(it, "target_skills", None):
                focus_skills.extend(it.target_skills)

        if not focus_skills:
            focus_skills = ["SKILL_CIRCUIT_ANALYSIS", "SKILL_POWER_ELECTRONICS"] if "EE" in (getattr(plan, "programme_id", "") or "") else ["SKILL_THERMODYNAMICS", "SKILL_PHYSICAL_METALLURGY"]
        target_course_ids = [it.course_id for it in prep_items if getattr(it, "course_id", None)]
        focus_skills = list(dict.fromkeys(focus_skills))

        is_mba = "MBA" in (getattr(plan, "goal_id", "") or "").upper() or "CAT" in (getattr(plan, "goal_name", "") or "").upper()
        
        candidate_tasks: List[DailyTask] = []
        days_label = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for day_idx in range(1, 8):
            skill_target = focus_skills[(day_idx - 1) % len(focus_skills)] if focus_skills else "GOAL_PREPARATION"
            
            if is_mba:
                if day_idx == 1:
                    task = DailyTask(
                        task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                        day_number=day_idx,
                        title=f"{days_label[day_idx-1]}: Quantitative Aptitude — Arithmetic & Algebra Speed Drills",
                        estimated_minutes=int(daily_hours * 60 * 0.6),
                        task_type="practice_exercise",
                        skill_id="SKILL_MBA_QUANT_APTITUDE",
                        exercise_id=f"EX_MBA_QA_W{week_number}_{day_idx}"
                    )
                elif day_idx == 2:
                    task = DailyTask(
                        task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                        day_number=day_idx,
                        title=f"{days_label[day_idx-1]}: Verbal Ability — Editorial Reading & Critical Reasoning Passages",
                        estimated_minutes=int(daily_hours * 60 * 0.5),
                        task_type="reading",
                        skill_id="SKILL_MBA_VERBAL_ABILITY",
                        resource_id="MBA-L1"
                    )
                elif day_idx == 3:
                    task = DailyTask(
                        task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                        day_number=day_idx,
                        title=f"{days_label[day_idx-1]}: DILR Practice — Matrix Logic & Tabular Caselet Sets",
                        estimated_minutes=int(daily_hours * 60 * 0.5),
                        task_type="practice_exercise",
                        skill_id="SKILL_MBA_DATA_INTERPRETATION",
                        exercise_id=f"EX_MBA_DILR_W{week_number}_{day_idx}"
                    )
                elif day_idx == 4:
                    task = DailyTask(
                        task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                        day_number=day_idx,
                        title=f"{days_label[day_idx-1]}: Sectional Mock Drill — 40-Minute Timed Sectional Simulation",
                        estimated_minutes=int(daily_hours * 60 * 0.6),
                        task_type="practice_exercise",
                        skill_id="SKILL_MBA_QUANT_APTITUDE",
                        exercise_id=f"EX_MBA_SECTIONAL_W{week_number}_{day_idx}"
                    )
                elif day_idx == 5:
                    task = DailyTask(
                        task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                        day_number=day_idx,
                        title=f"{days_label[day_idx-1]}: Profile & Business Awareness — Case Analysis & CV Action",
                        estimated_minutes=int(daily_hours * 60 * 0.4),
                        task_type="revision",
                        skill_id="SKILL_MBA_BUSINESS_AWARENESS"
                    )
                elif day_idx == 6:
                    task = DailyTask(
                        task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                        day_number=day_idx,
                        title=f"{days_label[day_idx-1]}: Weekly Checkpoint Quiz & Proctored Diagnostic Review",
                        estimated_minutes=int(daily_hours * 60 * 0.4),
                        task_type="quiz",
                        skill_id="SKILL_MBA_QUANT_APTITUDE"
                    )
                else:
                    task = DailyTask(
                        task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                        day_number=day_idx,
                        title=f"{days_label[day_idx-1]}: Rest / Buffer / Error Log Catch-up",
                        estimated_minutes=int(daily_hours * 60 * 0.3),
                        task_type="revision",
                        skill_id="SKILL_MBA_QUANT_APTITUDE"
                    )
            else:
                # Engineering & Career Domain Practice (Never a major lecture)
                if day_idx in [1, 2, 4]:
                    task = DailyTask(
                        task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                        day_number=day_idx,
                        title=f"{days_label[day_idx-1]}: Active Practice & Problem Set — {skill_target}",
                        estimated_minutes=int(daily_hours * 60 * 0.6),
                        task_type="practice_exercise",
                        skill_id=skill_target,
                        exercise_id=f"EX_{skill_target}_{week_number}_{day_idx}"
                    )
                elif day_idx in [3, 5]:
                    task = DailyTask(
                        task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                        day_number=day_idx,
                        title=f"{days_label[day_idx-1]}: Concept Review & Derivation Drill — {skill_target}",
                        estimated_minutes=int(daily_hours * 60 * 0.5),
                        task_type="revision",
                        skill_id=skill_target
                    )
                elif day_idx == 6:
                    task = DailyTask(
                        task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                        day_number=day_idx,
                        title=f"{days_label[day_idx-1]}: Weekly Mastery Gate & Checkpoint Quiz",
                        estimated_minutes=int(daily_hours * 60 * 0.4),
                        task_type="quiz",
                        skill_id=skill_target
                    )
                else: # Sunday
                    task = DailyTask(
                        task_id=f"TASK_W{week_number}_D{day_idx}_{uuid.uuid4().hex[:6]}",
                        day_number=day_idx,
                        title=f"{days_label[day_idx-1]}: Rest / Buffer / Project Implementation",
                        estimated_minutes=int(daily_hours * 60 * 0.3),
                        task_type="revision",
                        skill_id=skill_target
                    )
            candidate_tasks.append(task)

        # Budget enforcement
        kept_tasks: List[DailyTask] = []
        deferred_tasks: List[str] = []
        accumulated_minutes = 0

        if weekly_hours_budget is not None and weekly_hours_budget > 0:
            max_minutes = int(weekly_hours_budget * 60)
            for t in candidate_tasks:
                if accumulated_minutes + t.estimated_minutes <= max_minutes:
                    kept_tasks.append(t)
                    accumulated_minutes += t.estimated_minutes
                else:
                    deferred_tasks.append(f"{t.title} (Deferred: exceeds weekly budget of {weekly_hours_budget:.1f}h)")
        else:
            kept_tasks = candidate_tasks

        total_hours = sum(t.estimated_minutes for t in kept_tasks) / 60.0

        weekly_obj = (
            "Target CAT preparation drills across QA, VARC, and DILR with weekly mastery checkpoint"
            if is_mba else
            f"Master goal-targeted competencies in {', '.join(focus_skills[:2])}"
        )

        return WeeklyRoadmap(
            week_number=week_number,
            semester_number=semester_number,
            weekly_objective=weekly_obj,
            focus_skills=focus_skills,
            target_courses=target_course_ids,
            daily_tasks=kept_tasks,
            milestone_checkpoint=f"Week {week_number} Mastery Evaluation" if week_number % 4 == 0 else None,
            total_estimated_hours=round(total_hours, 1),
            weekly_hours_budget=weekly_hours_budget,
            deferred_tasks=deferred_tasks
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
        move_items = {m["item_id"]: m for m in mods.get("move_items", []) if "item_id" in m}
        replace_items = {r["replace_item_id"]: r for r in mods.get("replace_items", []) if "replace_item_id" in r}

        # Filter out removed courses and handle move / replace
        for it in old_items:
            if it.course_id and it.course_id in remove_courses:
                continue
            if it.item_id in replace_items:
                r_spec = replace_items[it.item_id]
                with_item = r_spec.get("with_item")
                if isinstance(with_item, PlanItem):
                    new_items.append(with_item)
                elif isinstance(with_item, dict):
                    new_items.append(PlanItem(**with_item))
                elif "course_id" in r_spec:
                    c_new = r_spec["course_id"]
                    new_items.append(it.model_copy(update={
                        "course_id": c_new,
                        "item_id": f"ITEM_REP_{c_new}_{uuid.uuid4().hex[:6]}",
                        "reason": StructuredReason(
                            intent=it.reason.intent,
                            target_skills=it.reason.target_skills,
                            why_this=f"Replaced {it.course_id} with {c_new} per approved proposal: {proposal.reasoning}",
                            prerequisite_for=it.reason.prerequisite_for,
                            rule_compliance=it.reason.rule_compliance
                        )
                    }))
                continue
            if it.item_id in move_items:
                m_spec = move_items[it.item_id]
                updates = {}
                if "target_semester" in m_spec:
                    updates["semester_number"] = m_spec["target_semester"]
                if "target_week" in m_spec:
                    updates["scheduled_week"] = m_spec["target_week"]
                    updates["week_index"] = m_spec["target_week"]
                new_items.append(it.model_copy(update=updates))
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

        req_courses = [it for it in new_items if it.item_type == "REQUIRED_COURSE" or (it.item_type == "course" and getattr(it, "status_badge", "") == "LOCKED")]
        rec_items = [it for it in new_items if it not in req_courses]

        candidate_plan = Plan(
            plan_id=f"PLAN_{student.student_id}_{uuid.uuid4().hex[:8]}",
            student_id=student.student_id,
            goal_id=current_plan.goal_id,
            version=current_plan.version + 1,
            items=new_items,
            required_courses=req_courses,
            recommended_items=rec_items,
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
