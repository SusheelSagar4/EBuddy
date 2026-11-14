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
    reason: StructuredReason

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
    is_active: bool = True
    created_at: datetime

