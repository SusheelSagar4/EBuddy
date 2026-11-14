from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from app.contracts.base import BaseContract

TaskType = Literal[
    'video_lecture',
    'reading',
    'practice_exercise',
    'quiz',
    'project',
    'revision'
]

class DailyTask(BaseContract):
    task_id: str
    day_number: int # 1 to 7
    title: str
    estimated_minutes: int = 45
    task_type: TaskType = 'video_lecture'
    skill_id: Optional[str] = None
    course_id: Optional[str] = None
    resource_id: Optional[str] = None
    resource_title: Optional[str] = None
    resource_url: Optional[str] = None
    exercise_id: Optional[str] = None
    is_completed: bool = False

class WeeklyRoadmap(BaseContract):
    week_number: int # 1 to 16
    semester_number: int
    weekly_objective: str
    focus_skills: List[str]
    target_courses: List[str]
    daily_tasks: List[DailyTask]
    milestone_checkpoint: Optional[str] = None
    total_estimated_hours: float = 0.0
    weekly_hours_budget: Optional[float] = None
    deferred_tasks: List[str] = []

class RoadmapVersionRecord(BaseContract):
    version_id: str
    plan_id: str
    student_id: str
    version_number: int
    commit_reason: str
    approved_proposal_id: Optional[str] = None
    total_items: int
    total_credits: float
    diff_summary: Optional[str] = None
    committed_at: datetime

