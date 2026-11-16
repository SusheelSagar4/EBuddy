from typing import Optional, List, Dict, Any, Literal
from app.contracts.base import BaseContract

class Course(BaseContract):
    course_id: str
    course_code: str
    display_code: str
    code_conflict: bool = False
    title: str
    department_id: Optional[str] = None
    credits: float
    ltp: Optional[str] = None
    mode: str = 'offline'
    level: str = 'UG'
    status: str = 'verified'
    source_id: str
    verified: bool = True

    def student_citation(self) -> str:
        """
        Cite display_code + title to students.
        Conflicting codes are shown with both titles and a 'code conflict' note.
        """
        base = f"{self.display_code} {self.title}"
        if self.code_conflict:
            return f"{base} [NOTE: Official curriculum uses code {self.display_code} for both Core and Elective options; referenced internally as {self.course_id}]"
        return base

class Module(BaseContract):
    module_id: str
    course_id: str
    title: str
    order_no: int = 1
    status: str = 'verified'
    source_id: str = 'PLACEHOLDER'
    verified: bool = False

class Resource(BaseContract):
    resource_id: str
    title: str
    url: str
    provider: str
    media_type: str # playlist, lecture, textbook, notes
    coverage_status: str # Playlist found, Partial / related only, Not confirmed, etc.
    link_verified: bool = False
    status: str = 'verified'
    source_id: str
    verified: bool = True

class Exercise(BaseContract):
    exercise_id: str
    skill_id: str
    course_id: Optional[str] = None
    title: str
    question_text: str
    exercise_type: Literal['mcq', 'numeric', 'short_answer', 'project']
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    difficulty_0_100: float = 50.0
    status: str = 'draft_for_review'
    source_id: str = 'SYNTHETIC_EXERCISE'
    verified: bool = False

class AcademicRule(BaseContract):
    rule_id: str
    rule_type: str # credit_cap, minor_eligibility, online_credit, prerequisite
    parameters: Dict[str, Any]
    human_text: str
    status: str = 'verified' # verified or unsourced_baseline
    source_id: str
    verified: bool = True

class ResearchProject(BaseContract):
    project_id: str
    title: str
    detail_level: str = 'full' # full, title_only
    status: str = 'verified'
    source_id: str
    verified: bool = True

class Skill(BaseContract):
    skill_id: str
    name: str
    domain: str
    description: str
    level_scale: str = '0-100'
    status: str = 'verified'
    source_id: str
    verified: bool = True

