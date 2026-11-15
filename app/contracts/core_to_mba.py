from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# General MBA Contracts (data/seed/mba/)
# ---------------------------------------------------------

class MBARoute(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    typical_timing: Optional[str] = None

class MBAExam(BaseModel):
    id: str
    name: str
    conducting_body: Optional[str] = None
    route_ids: Optional[str] = None
    pattern: Optional[str] = None
    total_questions: Optional[str] = None
    total_minutes: Optional[int] = None
    marking_scheme: Optional[str] = None
    score_scale: Optional[str] = None
    attempts_rule: Optional[str] = None
    eligibility: Optional[str] = None
    official_url: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class MBAExamCycle(BaseModel):
    exam_id: str
    cycle: str
    organiser: Optional[str] = None
    reg_open: Optional[str] = None
    reg_close: Optional[str] = None
    exam_dates: Optional[str] = None
    admit_card_date: Optional[str] = None
    result_date: Optional[str] = None
    fee: Optional[str] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class MBAExamSection(BaseModel):
    exam_id: str
    section: str
    questions: Optional[str] = None
    minutes: Optional[int] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class MBASyllabusTopic(BaseModel):
    id: str
    exam_id: str
    section: str
    topic: str
    subtopics: Optional[str] = None
    source_type: str = "team_curated"
    verified: bool = False
    verified_by: Optional[str] = None

class MBAInstitution(BaseModel):
    id: str
    name: str
    type: Optional[str] = None # IIM, B-school, University department
    city: Optional[str] = None
    official_url: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class MBAProgramme(BaseModel):
    id: str
    institution_id: str
    programme_name: str
    degree: Optional[str] = None
    duration_months: Optional[int] = None
    exams_accepted: Optional[str] = None
    work_ex_policy: Optional[str] = None
    selection_process: Optional[str] = None
    application_deadline: Optional[str] = None
    fees: Optional[str] = None
    official_url: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class MBAAdmissionStat(BaseModel):
    programme_id: str
    year: int
    category: str
    stage: str
    cutoff_value: float
    cutoff_type: str # percentile, scaled_score
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class MBAMilestone(BaseModel):
    id: str
    route_id: str
    name: str
    typical_timing: Optional[str] = None
    depends_on: Optional[str] = None
    exam_id: Optional[str] = None

class MBAPrepTemplate(BaseModel):
    id: str
    exam_id: Optional[str] = None
    speed_months: int
    weekly_hours: int
    phases_summary: Optional[str] = None
    readiness_rule: Optional[str] = None

class MBATemplatePhase(BaseModel):
    template_id: str
    order: int
    name: str
    share_of_weeks: float
    sections: Optional[str] = None
    checkpoint: Optional[str] = None

class MBAPracticeItem(BaseModel):
    id: str
    exam_id: Optional[str] = None
    section: str
    topic: str
    difficulty: float = 1.0
    type: str = "numeric" # numeric / mcq
    stem: str
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    answer: str
    explanation: Optional[str] = None
    source_type: str = "team_written"
    reviewed: bool = False
    reviewed_by: Optional[str] = None

class MBAInterviewQuestion(BaseModel):
    id: str
    category: str
    question: str
    what_good_looks_like: Optional[str] = None
    source_type: str = "team_written"

class MBAInterviewRubric(BaseModel):
    criterion: str
    score_1: str
    score_2: str
    score_3: str
    score_4: str

class MBAApplicationChecklistItem(BaseModel):
    id: str
    item: str
    applies_to: str

class MBALearningMethod(BaseModel):
    id: str
    name: str
    when_to_use: Optional[str] = None
    how: Optional[str] = None

class MBAResource(BaseModel):
    id: str
    title: str
    url: str
    provider: Optional[str] = None
    type: Optional[str] = None
    exam_ids: Optional[str] = None
    free: bool = True

# ---------------------------------------------------------
# Core to MBA Specific Contracts (data/seed/core_to_mba/)
# ---------------------------------------------------------

class CareerPath(BaseModel):
    id: str
    branch: str # EE, MM, any
    name: str
    description: str
    typical_roles: str
    skills_valued: str
    sectors: str
    source_type: str = "team_curated"
    reviewed: bool = False
    reviewed_by: Optional[str] = None

class BranchPITopic(BaseModel):
    id: str
    branch: str
    topic: str
    subtopics: Optional[str] = None
    interview_level_notes: Optional[str] = None
    reviewed: bool = False
    reviewed_by: Optional[str] = None

class BranchPIQuestion(BaseModel):
    id: str
    branch: str
    topic_id: str
    question: str
    what_good_looks_like: str
    source_type: str = "team_curated"
    reviewed: bool = False
    reviewed_by: Optional[str] = None

class ProfileAuditRubric(BaseModel):
    criterion: str
    level_1: str
    level_2: str
    level_3: str
    level_4: str

class ProfileAction(BaseModel):
    id: str
    branch: str
    action: str
    criterion_improved: str
    effort_hours: int
    timing: Optional[str] = None
    course_code: Optional[str] = None
    reviewed: bool = False
    reviewed_by: Optional[str] = None

class StoryDraft(BaseModel):
    id: Optional[int] = None
    student_id: str
    kind: str # why_mba, why_not_core, project_story, leadership_story
    version: int = 1
    text: str
    rubric_scores: Dict[str, int] = Field(default_factory=dict)
    feedback: Optional[str] = None
    created_at: Optional[str] = None

class DecisionOption(BaseModel):
    student_id: str
    option: str # stay_core_research, stay_core_industry, mtech_gate, mba_now, mba_after_work
    name: str
    timeline: Dict[str, Any] = Field(default_factory=dict)
    tradeoffs: str
    requirements: List[str] = Field(default_factory=list)
    clashes: List[str] = Field(default_factory=list)
    chosen: bool = False
    decided_at: Optional[str] = None

class ScoreBand(BaseModel):
    min_score: float
    max_score: float
    mean_score: float
    confidence_level: float = 0.8
    is_estimated: bool = True
    uncertainty_note: str = "Estimated percentile range based on simulated/raw mock test distributions. Does not guarantee admission."
    num_mocks_used: int = 0

class ShortlistProgramme(BaseModel):
    programme_id: str
    programme_name: str
    institution_id: str
    institution_name: str
    tier: str # reach, target, safe
    closing_cutoff: float
    cutoff_type: str
    cutoff_year: int
    cutoff_source: str
    application_deadline: Optional[str] = None
    is_verified: bool = False

class ShortlistResult(BaseModel):
    reach: List[ShortlistProgramme] = Field(default_factory=list)
    target: List[ShortlistProgramme] = Field(default_factory=list)
    safe: List[ShortlistProgramme] = Field(default_factory=list)
    generated_at: str
    disclaimer: str = "Estimates only based on verified past closing cut-offs. Admission is subject to GD/WAT/PI performance and institute category policies."
