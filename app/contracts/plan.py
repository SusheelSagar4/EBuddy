from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from app.contracts.base import BaseContract

class StructuredReason(BaseContract):
    intent: str # e.g. "Core degree completion", "Bridge skill gap", "Exam preparation"
    target_skills: List[str]
    why_this: str
    prerequisite_for: List[str] = []
    rule_compliance: List[str] = []

class PlanItem(BaseContract):
    item_id: str
    item_type: Literal['course', 'exercise', 'resource', 'milestone', 'remediation']
    course_id: Optional[str] = None # internally tracked by surrogate course_id
    exercise_id: Optional[str] = None
    resource_id: Optional[str] = None
    semester_number: Optional[int] = None
    scheduled_week: Optional[int] = None
    estimated_hours: float = 0.0
    phase: Optional[str] = None # 'Phase 1: Foundation', 'Phase 2: Core Depth', 'Phase 3: Applied Mastery'
    prep_hours_weekly: Optional[float] = None
    reason: StructuredReason
    # --- v1.4.0 additions (optional, backwards compatible) ---
    title: Optional[str] = None            # human-readable title resolved from the KB (never LLM-written)
    credits: Optional[float] = None        # course credits copied from kb.course
    track_id: Optional[str] = None         # career track (sde / da / aiml) this item belongs to
    track_phase_id: Optional[str] = None   # phase id inside the career-track roadmap
    url: Optional[str] = None              # KB resource URL (resource items only)
    planning_status: Optional[str] = None  # current | planned | deferred | beyond_horizon

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
    # v1.4.0: what triggered the re-plan and the deterministic reasons behind each change
    trigger: Optional[str] = None
    reasons: List[str] = []

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
    # v1.4.0: evidence-weight ledger, multi-semester horizon summary and persona advisories
    evidence_summary: Optional[Dict[str, Any]] = None
    horizon: Optional[Dict[str, Any]] = None
    advisories: List[str] = []
    is_active: bool = True
    created_at: datetime

