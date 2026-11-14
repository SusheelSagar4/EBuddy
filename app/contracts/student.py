from typing import Optional, Dict, Any, Literal
from datetime import datetime
from app.contracts.base import BaseContract

class StudentProfile(BaseContract):
    student_id: str
    name: str
    programme_id: str
    current_semester: int
    cgpa: Optional[float] = None
    backlogs: int = 0
    is_synthetic: bool = False
    created_at: Optional[datetime] = None

class EvidenceItem(BaseContract):
    evidence_id: str
    student_id: str
    skill_id: str
    source_type: Literal['diagnostic', 'exercise', 'quiz', 'course_grade', 'self_declaration']
    score: float # 0.0 to 100.0
    reliability: float = 1.0 # 0.0 to 1.0
    attempts: int = 1
    time_spent_min: Optional[int] = None
    recorded_at: datetime

class SkillState(BaseContract):
    student_id: str
    skill_id: str
    estimated_level: float # 0.0 to 100.0
    confidence: float # 0.0 to 1.0
    last_updated: datetime

class Constraint(BaseContract):
    constraint_id: str
    student_id: str
    constraint_type: str # e.g., max_weekly_hours, no_late_classes
    parameters: Dict[str, Any]
    is_active: bool = True

class Preference(BaseContract):
    preference_id: str
    student_id: str
    preference_type: str # e.g., learning_style, resource_format
    value: str
    weight: float = 1.0

