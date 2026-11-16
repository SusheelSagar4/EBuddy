from typing import Optional, Dict, Any
from app.contracts.base import BaseContract

class Goal(BaseContract):
    goal_id: str
    name: str
    category: str # career, higher_studies, competitive_exam, startup
    description: str
    status: str = 'verified' # verified, draft_for_review, unsourced_baseline
    source_id: str
    verified: bool = True

class GoalRequirement(BaseContract):
    goal_id: str
    skill_id: str
    required_level: float # 0.0 to 100.0
    importance: float = 1.0 # 0.0 to 1.0
    status: str = 'verified'
    source_id: str
    verified: bool = True

class MasteryCriteria(BaseContract):
    criteria_id: str
    goal_id: str
    skill_id: Optional[str] = None
    criteria: Dict[str, Any] # e.g. min_skill_level, required_project_milestones, required_timed_assessments
    status: str = 'verified'
    source_id: str
    verified: bool = True

class Milestone(BaseContract):
    milestone_id: str
    goal_id: str
    semester_target: int
    title: str
    description: str
    status: str = 'verified'
    source_id: str
    verified: bool = True

