from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime

class Route(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

class Exam(BaseModel):
    id: str
    name: str
    conducting_body: Optional[str] = None
    route_ids: Optional[str] = None
    pattern_json: Optional[str] = None
    marking_scheme: Optional[str] = None
    score_scale: Optional[str] = None
    score_validity_years: int = 3
    official_url: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    cycle: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class ExamCycle(BaseModel):
    id: str
    exam_id: str
    cycle: str
    organiser: Optional[str] = None
    reg_open: Optional[str] = None
    reg_close: Optional[str] = None
    exam_dates: Optional[str] = None
    admit_card_date: Optional[str] = None
    result_date: Optional[str] = None
    fee: Optional[float] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class ExamPaper(BaseModel):
    id: str
    exam_id: str
    paper_code: str
    name: str
    branches_mapped: str
    allowed_second_papers: Optional[str] = None
    syllabus_url: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    cycle: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class SyllabusTopic(BaseModel):
    id: str
    paper_code: str
    section: str # General Aptitude, Engineering Mathematics, Core
    topic: str
    subtopics: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    cycle: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class TopicWeightage(BaseModel):
    id: str
    paper_code: str
    topic_id: str
    year: int
    marks: float
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    cycle: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class CourseTopicMap(BaseModel):
    id: str
    course_code: str
    topic_id: str
    coverage: str = "partial" # full / partial
    reviewed_by: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    cycle: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class PYQItem(BaseModel):
    id: str
    paper_code: str
    year: int
    topic_id: str
    question_ref: str
    marks: float = 1.0
    type: str = "MCQ" # MCQ / MSQ / NAT
    answer_key_source: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    cycle: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class Institution(BaseModel):
    id: str
    name: str
    type: str # IIT / IISc / NIT / IIIT / other
    city: Optional[str] = None
    official_url: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    cycle: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class HigherProgramme(BaseModel):
    id: str
    institution_id: str
    degree: str # M.Tech / ME / MS(R) / Direct PhD
    department: str
    specialisation: str
    exams_accepted: Optional[str] = None
    gate_papers_accepted: Optional[str] = None
    branches_eligible: Optional[str] = None
    min_qualifying_criteria: Optional[str] = None
    selection_mode: str = "GATE score" # GATE score / written test / interview
    application_portal: str = "COAP" # COAP / CCMT / institute
    application_deadline: Optional[str] = None
    fees: Optional[float] = None
    stipend_or_assistantship: Optional[str] = None
    research_areas: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    cycle: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class AdmissionStat(BaseModel):
    id: str
    programme_id: str
    year: int
    category: str # GEN / OBC-NCL / EWS / SC / ST / PwD
    round: str
    closing_score_or_rank: float
    score_type: str = "GATE score" # GATE score / AIR
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    cycle: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class PSU(BaseModel):
    id: str
    name: str
    recruits_via_gate: bool = True
    disciplines: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    cycle: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class PSUCycle(BaseModel):
    id: str
    psu_id: str
    cycle: str
    gate_year_used: Optional[int] = None
    application_window: Optional[str] = None
    disciplines: Optional[str] = None
    past_cutoff: Optional[float] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class CounsellingCycle(BaseModel):
    id: str
    portal: str # COAP / CCMT
    cycle: str
    round_dates: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class PrepTemplate(BaseModel):
    id: str
    paper_code: str
    speed_months: int # 12 / 6 / 3
    readiness_rule_json: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    cycle: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class TemplatePhase(BaseModel):
    id: str
    template_id: str
    phase_order: int
    name: str
    share_of_weeks: float
    topic_selector: Optional[str] = None
    checkpoint: Optional[str] = None
    activities: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "official"
    retrieved_on: Optional[str] = None
    cycle: Optional[str] = None
    verified: bool = False
    verified_by: Optional[str] = None

class MockResult(BaseModel):
    id: str
    student_id: str
    mock_id: str
    kind: str # topic test / subject test / full mock / official result
    score: float
    max_score: float = 100.0
    percentile: Optional[float] = None
    time_taken: Optional[int] = None # minutes
    topic_breakdown_json: Optional[str] = None
    taken_on: Optional[str] = None

class ErrorLogItem(BaseModel):
    id: str
    student_id: str
    item_ref: str
    topic_id: str
    mistake_type: str # concept / calculation / reading / time
    created_at: Optional[str] = None

class StudentApplication(BaseModel):
    id: str
    student_id: str
    target_id: str # programme_id or psu_id
    target_type: str = "programme" # programme / psu
    tier: Optional[str] = None # Reach / Target / Safe
    status: str = "draft" # draft / submitted / shortlisted / offered / rejected
    checklist_json: Optional[str] = None
    deadline: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class InterviewSession(BaseModel):
    id: str
    student_id: str
    programme_id: Optional[str] = None
    kind: str = "technical" # technical / research
    transcript_summary: Optional[str] = None
    rubric_scores: Optional[str] = None
    feedback: Optional[str] = None
    created_at: Optional[str] = None

class GATEResult(BaseModel):
    id: str
    student_id: str
    cycle: str
    paper_code: str
    score: float
    rank: Optional[int] = None
    verified_by_student: bool = True
    created_at: Optional[str] = None

# Value Objects & Analysis Models
class EligibilityResult(BaseModel):
    is_eligible: bool
    status: str # eligible / eligible_later / ineligible
    when_eligible: Optional[str] = None
    rule_id: str
    rule_text: str
    rule_source: str
    reasons: List[str] = Field(default_factory=list)
    allowed_second_papers: List[str] = Field(default_factory=list)
    best_valid_option: Optional[str] = None

class ScoreBand(BaseModel):
    min_score: float
    max_score: float
    mean_score: float
    confidence_level: float = 0.8
    is_estimated: bool = True
    uncertainty_note: str
    num_mocks_used: int

class ProgrammeTier(BaseModel):
    programme_id: str
    institution_name: str
    degree: str
    specialisation: str
    tier: str # Reach / Target / Safe / unknown
    fit_reason: str
    past_closing_range: Optional[str] = None
    closing_scores_by_year: Dict[int, float] = Field(default_factory=dict)
    verified_deadline: Optional[str] = None
    selection_mode: str
    stipend: Optional[str] = None
    source_citation: Optional[str] = None
    is_verified: bool = False

class Shortlist(BaseModel):
    reach: List[ProgrammeTier] = Field(default_factory=list)
    target: List[ProgrammeTier] = Field(default_factory=list)
    safe: List[ProgrammeTier] = Field(default_factory=list)
    unknown: List[ProgrammeTier] = Field(default_factory=list)
    balanced_recommendation: List[str] = Field(default_factory=list)

class ConflictAlert(BaseModel):
    kind: str # placement_clash / exam_clash / deadline_clash
    title: str
    date_window: str
    severity: str # high / medium / warning
    options: List[str] = Field(default_factory=list)
    trade_off_description: str
