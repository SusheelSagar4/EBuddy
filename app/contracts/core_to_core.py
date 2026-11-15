from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict
from app.contracts.base import BaseContract

class AcademicCalendarWeek(BaseContract):
    semester: str
    week_number: int
    week_start: str
    week_type: str # teaching, midsem, endsem, break, holiday
    calendar_factor: float
    source_url: str
    verified: bool = True

class ResearchArea(BaseContract):
    area_id: str
    name: str
    department: str
    description: str
    parent_area_id: Optional[str] = None

class AreaSkill(BaseContract):
    area_id: str
    skill_id: str
    required_level: float

class Faculty(BaseContract):
    id: str
    name: str
    department: str
    designation: str
    lab_name: Optional[str] = None
    profile_url: str
    email_public: Optional[str] = None
    takes_ug_students: str = "unknown" # yes, no, unknown
    source_url: str
    retrieved_on: str
    verified: bool = True

class FacultyArea(BaseContract):
    faculty_id: str
    area_id: str
    weight: float = 1.0

class Paper(BaseContract):
    id: str
    title: str
    year: int
    venue: str
    doi_or_url: str
    abstract: Optional[str] = None
    open_access: bool = False
    licence: Optional[str] = None
    fulltext_path: Optional[str] = None
    source_url: str
    retrieved_on: str
    verified: bool = True

class PaperChunk(BaseContract):
    chunk_id: str
    paper_id: str
    page: int
    chunk_index: int
    text: str

class PaperSkill(BaseContract):
    paper_id: str
    skill_id: str
    level: float
    reviewed: bool = True

class TasterTask(BaseContract):
    id: str
    area_id: str
    kind: str # read_abstract, solve_problem, short_writeup
    prompt: str
    rubric: str
    est_minutes: int

class IndustryMilestone(BaseContract):
    id: str
    department: str
    name: str
    kind: str # exam, tool_skill, project_club, internship
    typical_timing: str
    related_exam_id: Optional[str] = None
    source_url: Optional[str] = None

class WeeklyFocusItem(BaseModel):
    focus_id: str
    category: str # core_course, research_skill, industry_tool, remedial
    target_id: str # course_code or skill_id
    title: str
    activity: str
    suggested_hours: float
    why: str

class WeeklyFocusPlan(BaseModel):
    student_id: str
    week_number: int
    week_start: str
    week_type: str
    budget_hours: float
    calendar_factor: float
    focus_items: List[WeeklyFocusItem]
    cgpa_protection_active: bool = False
    cgpa_protection_reason: Optional[str] = None
    version: int = 1

class ReflectionSubmission(BaseModel):
    week_number: int
    week_start: str
    worked: str
    didnt_work: str
    self_rating: int # 1 to 5
    hours_spent: float

class FacultyMatch(BaseModel):
    faculty_id: str
    name: str
    department: str
    designation: str
    lab_name: Optional[str] = None
    profile_url: str
    takes_ug_students: str
    match_score: float
    score_breakdown: Dict[str, float]
    overlapping_areas: List[str]
    cited_papers: List[Dict[str, Any]]
    match_reason: str

class ApproachDraft(BaseModel):
    student_id: str
    faculty_id: str
    faculty_name: str
    draft_email: str
    cv_bullets: List[str]
    interview_questions: List[str]
    status: str = "drafted" # drafted, sent, no_reply, meeting_scheduled, accepted, declined
    days_since_sent: int = 0
    followup_recommended: bool = False
    alternative_faculty_id: Optional[str] = None

class ResearchMilestone(BaseModel):
    milestone_id: str
    title: str
    phase: str
    description: str
    target_week: str
    deliverable: str
    status: str = "pending" # pending, in_progress, completed

class ResearchLogEntry(BaseModel):
    entry_id: str
    student_id: str
    week_number: int
    summary: str
    findings: str
    blockers: Optional[str] = None
    created_at: str

class ReadinessGateResult(BaseModel):
    passed: bool
    student_id: str
    foundation_skills_met: bool
    foundation_skills_details: Dict[str, Any]
    taster_tasks_met: bool
    taster_tasks_completed: int
    taster_tasks_avg_score: float
    paper_summary_met: bool
    paper_summary_score: float
    reasons: List[str]
