from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from app.contracts.base import BaseContract

ItemType = Literal[
    'course',
    'exercise',
    'resource',
    'milestone',
    'remediation',
    'REQUIRED_COURSE',
    'ELECTIVE_PICK',
    'RESOURCE',
    'EXERCISE_SET',
    'PROJECT',
    'RESEARCH_TASTER',
    'CHECKPOINT',
    'BUFFER_EXAM_WEEK'
]

class StructuredReason(BaseContract):
    intent: str # e.g. "Core degree completion", "Bridge skill gap", "Exam preparation"
    target_skills: List[str]
    why_this: str
    prerequisite_for: List[str] = []
    rule_compliance: List[str] = []

class PlanItem(BaseContract):
    item_id: str
    item_type: ItemType
    course_id: Optional[str] = None # internally tracked by surrogate course_id
    exercise_id: Optional[str] = None
    resource_id: Optional[str] = None
    semester_number: Optional[int] = None
    scheduled_week: Optional[int] = None
    estimated_hours: float = 0.0
    phase: Optional[str] = None # 'Phase 1: Foundation', 'Phase 2: Core Depth', 'Phase 3: Applied Mastery'
    prep_hours_weekly: Optional[float] = None
    reason: StructuredReason

    # Roadmap v2 Timeline & Grounding Attributes
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    week_index: Optional[int] = None
    is_indicative: bool = False
    hours_per_week: float = 0.0
    skill_gap_reason: Optional[str] = None
    cited_kb_codes: List[str] = []
    status_badge: str = "RECOMMENDED" # "LOCKED", "RECOMMENDED", "OPTIONAL"
    goal_emphasis: Optional[str] = None
    slot_id: Optional[str] = None
    pool_rule_status: Optional[str] = None

class WeeklyScheduleItem(BaseContract):
    item_id: str
    item_type: str
    title: str
    hours_per_week: float
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    week_index: int
    is_indicative: bool = False
    skill_gap_reason: Optional[str] = None
    cited_kb_codes: List[str] = []
    status_badge: str = "RECOMMENDED"
    details: Dict[str, Any] = {}

class MonthlyTheme(BaseContract):
    month_index: int
    theme_name: str
    focus_skills: List[str] = []
    checkpoint: Optional[Dict[str, Any]] = None
    weekly_hours_cap: float = 20.0
    items: List[PlanItem] = []

class SemesterBlock(BaseContract):
    semester_number: int
    semester_name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_indicative: bool = False
    required_courses: List[PlanItem] = []
    elective_picks: List[PlanItem] = []
    monthly_themes: List[MonthlyTheme] = []
    total_credits: float = 0.0
    buffer_exam_weeks: List[int] = []

class TimelineRoadmap(BaseContract):
    plan_id: str
    student_id: str
    goal_id: str
    horizon_deadline: str
    semester_blocks: List[SemesterBlock] = []
    next_4_weeks: List[WeeklyScheduleItem] = []
    assumptions: Dict[str, Any] = {}

class ValidationCheck(BaseContract):
    check_name: str
    passed: bool
    severity: Literal['error', 'warning', 'info'] = 'error'
    message: str

class ValidationReport(BaseContract):
    plan_id: str
    passed: bool
    checks: List[ValidationCheck]
    messages: List[str]

class PlanDiff(BaseContract):
    previous_plan_id: str
    new_plan_id: str
    added_items: List[PlanItem] = []
    removed_items: List[PlanItem] = []
    modified_items: List[Dict[str, Any]] = []
    summary: str

class Plan(BaseContract):
    plan_id: str
    student_id: str
    goal_id: str
    version: int = 1
    items: List[PlanItem]
    validation_report: Optional[ValidationReport] = None
    conflict_flag: Optional[str] = None
    optional_overload_proposals: List[Dict[str, Any]] = []
    plan_diff: Optional[PlanDiff] = None
    what_changed_and_why: Optional[str] = None
    mismatch_warning: Optional[Dict[str, Any]] = None
    is_active: bool = True
    created_at: datetime

    # Roadmap v2 Top-Level Structured Timeline & Classification
    timeline_roadmap: Optional[TimelineRoadmap] = None
    semester_blocks: List[SemesterBlock] = []
    next_4_weeks: List[WeeklyScheduleItem] = []
    required_courses: List[PlanItem] = []
    recommended_items: List[PlanItem] = []
    workload_cap_explanation: Optional[str] = None
