import uuid
from typing import List, Dict, Any, Optional, Set, Tuple
from app.contracts.student import StudentProfile
from app.contracts.roadmap import WeeklyRoadmap, DailyTask
from app.kb.field_repo import field_repo
from app.engine.budget import BudgetEngine

class FieldPlannerEngine:
    """
    Deterministic Field Topic Planner & Capacity Model (Requirement F3).
    
    Capacity Model:
    1. In-class contact hours = sum(L + T + P) of enrolled courses via BudgetEngine.
    2. Base Free Hours = max(6.0, 24.0 - 0.4 * contact_hours).
       - Higher classes (contact hours) -> fewer free hours.
       - Fewer classes / free weeks -> more free hours.
    3. Calendar Factor adjustment:
       - Regular teaching weeks: 1.0
       - Midsem week (Week 8): 0.4
       - Endsem weeks (Weeks 15-16): 0.2
    4. CGPA Protection:
       - If CGPA < 7.5 or backlogs > 0: Free hours throttled by 50% to protect core academic grades.
    5. Topic Allocation Bounds:
       - Minimum: 1 topic/week (ensures forward progress)
       - Maximum: 4 topics/week (prevents student burnout)
    6. Unfinished / overflowing topics are preserved as deferred_tasks for subsequent weeks.
    """
    def __init__(self, budget_engine: Optional[BudgetEngine] = None):
        self.field_repo = field_repo
        self.budget_engine = budget_engine or BudgetEngine()

    def compute_weekly_capacity(
        self,
        student: StudentProfile,
        enrolled_course_ids: List[str],
        current_week: int = 1,
        hours_override: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates deterministic study hour capacity for field topics.
        """
        if hours_override is not None:
            return {
                "available_hours": max(2.0, float(hours_override)),
                "contact_hours": 0.0,
                "calendar_factor": 1.0,
                "cgpa_protection_active": False,
                "explanation": f"Custom one-week capacity override applied ({hours_override:.1f} hours)."
            }

        # 1. Contact hours
        contact_hours = self.budget_engine.compute_contact_hours(enrolled_course_ids)
        
        # 2. Base free hours
        base_free = max(6.0, 24.0 - (0.4 * contact_hours))

        # 3. Calendar factor
        cal_week = self.budget_engine.get_calendar_week(current_week)
        cal_factor = cal_week.calendar_factor

        available_hours = base_free * cal_factor

        # 4. CGPA Protection
        student_cgpa = float(student.cgpa) if student.cgpa is not None else 8.0
        cgpa_protection = (student_cgpa < 7.5) or (student.backlogs > 0)
        if cgpa_protection:
            available_hours *= 0.5

        available_hours = round(max(3.0, available_hours), 1)

        expl = (
            f"Capacity model: {base_free:.1f}h base free budget (from {contact_hours:.1f}h contact classes) "
            f"x {cal_factor} calendar factor ({cal_week.week_type})"
        )
        if cgpa_protection:
            expl += " - 50% CGPA protection throttle active."

        return {
            "available_hours": available_hours,
            "contact_hours": contact_hours,
            "calendar_factor": cal_factor,
            "cgpa_protection_active": cgpa_protection,
            "explanation": expl
        }

    def plan_weekly_field_topics(
        self,
        student: StudentProfile,
        field_id: str,
        week_number: int,
        semester_number: int,
        enrolled_course_ids: Optional[List[str]] = None,
        completed_topic_ids: Optional[Set[str]] = None,
        deferred_topic_ids: Optional[List[str]] = None,
        weak_topic_ids: Optional[Set[str]] = None,
        hours_override: Optional[float] = None
    ) -> WeeklyRoadmap:
        """
        Selects and schedules field topics into a 7-day WeeklyRoadmap adhering to capacity limits.
        """
        enrolled = enrolled_course_ids or []
        completed = set(completed_topic_ids or [])
        deferred = list(deferred_topic_ids or [])
        weak = set(weak_topic_ids or [])

        # 1. Determine available hours
        capacity = self.compute_weekly_capacity(student, enrolled, week_number, hours_override)
        available_hours = capacity["available_hours"]

        # 2. Retrieve all field topics in DAG order
        all_topics = self.field_repo.get_topics(field_id)

        # 3. Build candidate queue
        # Priority 1: Weak topics needing revision
        # Priority 2: Deferred tasks from previous weeks
        # Priority 3: Next uncompleted topics whose prerequisites are satisfied
        scheduled_topics: List[Dict[str, Any]] = []
        carried_deferred: List[str] = []
        allocated_hours = 0.0

        # Queue candidate items
        candidate_queue: List[Tuple[Dict[str, Any], bool]] = [] # (topic_dict, is_revision)

        # Add weak topics for revision
        for tid in weak:
            top = self.field_repo.get_topic_by_id(tid)
            if top:
                rev_top = dict(top)
                rev_top["title"] = f"[Revision] {top['title']}"
                rev_top["est_hours"] = min(4.0, top["est_hours"] * 0.5)
                candidate_queue.append((rev_top, True))

        # Add deferred topics
        for tid in deferred:
            top = self.field_repo.get_topic_by_id(tid)
            if top and top["topic_id"] not in completed:
                candidate_queue.append((top, False))

        # Add fresh topics
        for top in all_topics:
            tid = top["topic_id"]
            if tid in completed or any(c[0]["topic_id"] == tid for c in candidate_queue):
                continue
            prereqs = top.get("prerequisite_topic_ids", [])
            # Prereq check: all prereqs must be in completed
            if all(p in completed for p in prereqs):
                candidate_queue.append((top, False))

        # Clamping constants
        min_topics = 1 if capacity["calendar_factor"] > 0.2 else 0
        max_topics = 4

        # Greedily allocate topics up to available hours
        for top, is_rev in candidate_queue:
            cost = top["est_hours"]
            if (allocated_hours + cost <= available_hours and len(scheduled_topics) < max_topics) or len(scheduled_topics) < min_topics:
                scheduled_topics.append(top)
                allocated_hours += cost
            else:
                if not is_rev and top["topic_id"] not in carried_deferred:
                    carried_deferred.append(top["topic_id"])

        # Create suggested daily tasks for the 7 days (suggested only, zero rigid hour bookings)
        daily_tasks: List[DailyTask] = []
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Distribute scheduled topics across the week
        t_idx = 0
        for day_num in range(1, 8):
            day_name = day_names[day_num - 1]
            if scheduled_topics:
                curr_topic = scheduled_topics[t_idx % len(scheduled_topics)]
                t_idx += 1
                task_type = "revision" if "[Revision]" in curr_topic["title"] else "video_lecture"
                daily_tasks.append(DailyTask(
                    task_id=f"TASK_W{week_number}_D{day_num}_{uuid.uuid4().hex[:6]}",
                    day_number=day_num,
                    title=f"{day_name} Focus: {curr_topic['title']}",
                    estimated_minutes=int((curr_topic["est_hours"] / 2.0) * 60),
                    task_type=task_type,
                    skill_id=curr_topic.get("skill_id"),
                    resource_title=curr_topic.get("resource_title"),
                    resource_url=curr_topic.get("resource_url"),
                    is_completed=False
                ))

        focus_skills = list(dict.fromkeys([t.get("skill_id") for t in scheduled_topics if t.get("skill_id")]))

        return WeeklyRoadmap(
            week_number=week_number,
            semester_number=semester_number,
            weekly_objective=(
                f"Week {week_number} Plan for {field_id}: Complete {len(scheduled_topics)} focus topic(s) "
                f"within {available_hours:.1f}h allocated budget ({capacity['explanation']})."
            ),
            focus_skills=focus_skills,
            target_courses=enrolled,
            daily_tasks=daily_tasks,
            milestone_checkpoint=f"Topic Milestone: {scheduled_topics[-1]['title']}" if scheduled_topics else "Review Milestone",
            total_estimated_hours=round(allocated_hours, 1),
            weekly_hours_budget=available_hours,
            deferred_tasks=carried_deferred
        )

field_planner_engine = FieldPlannerEngine()
