from typing import Optional, Dict, Any, List, Literal
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
    # --- v1.4.0 additions (all optional, backwards compatible) ---
    year: Optional[int] = None                 # 1..4, derived from current_semester when absent
    first_year_track: str = "A"                # institute first-year common-core track (A or B)
    edge_case_tags: List[str] = []             # e.g. ACTIVE_BACKLOG, CGPA_ON_MINOR_CUTOFF, INTEREST_EVIDENCE_CLASH
    aims: Optional[str] = None                 # free-text self-declared aspiration (WEAK evidence)

class EvidenceItem(BaseContract):
    evidence_id: str
    student_id: str
    skill_id: str
    source_type: Literal[
        'diagnostic', 'exercise', 'quiz', 'course_grade', 'self_declaration',
        # v1.4.0: demonstrated-proficiency evidence kinds (PS 2.5)
        'timed_quiz', 'project_rubric', 'mock_interview'
    ]
    score: float # 0.0 to 100.0
    reliability: float = 1.0 # 0.0 to 1.0
    attempts: int = 1
    time_spent_min: Optional[int] = None
    recorded_at: datetime
    # v1.4.0: explicit evidence reliability tier (PS Section 4).
    # 'strong' = assessed (grades, diagnostics, timed quizzes, rubric projects, mock interviews)
    # 'medium' = untimed practice; 'weak' = self-declared interest / self-rating.
    # None => derived from source_type by app.engine.skill_state.reliability_tier_for().
    reliability_tier: Optional[Literal['strong', 'medium', 'weak']] = None
    notes: Optional[str] = None

class SkillState(BaseContract):
    student_id: str
    skill_id: str
    estimated_level: float # 0.0 to 100.0
    confidence: float # 0.0 to 1.0
    last_updated: datetime
    # v1.4.0: how much of this estimate rests on strong vs weak evidence
    strong_evidence_count: int = 0
    weak_evidence_count: int = 0
    evidence_basis: Optional[Literal['strong', 'medium', 'weak', 'mixed']] = None
    latest_assessed_score: Optional[float] = None    # most recent assessed (non self-declared) score
    latest_assessed_source: Optional[str] = None

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

