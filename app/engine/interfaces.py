from typing import Protocol, List, Dict, Any, Optional
from app.contracts.student import StudentProfile, EvidenceItem, SkillState, Constraint, Preference
from app.contracts.goal import Goal, GoalRequirement, MasteryCriteria
from app.contracts.plan import Plan, PlanItem, ValidationReport, PlanDiff
from app.contracts.kb import Course, Skill, Resource, Exercise, AcademicRule

class IRuleEngine(Protocol):
    """Executes kb.academic_rule + prerequisite/offering/slot checks."""
    def check_prerequisites(self, course_id: str, completed_course_ids: List[str]) -> bool: ...
    def check_credit_cap(self, student: StudentProfile, total_semester_credits: float) -> bool: ...
    def check_minor_eligibility(self, student: StudentProfile) -> bool: ...

class ISkillStateUpdater(Protocol):
    """Evidence ledger -> SkillState (weighted by source_type, recency, attempts)."""
    def update_states(self, student_id: str, evidence_items: List[EvidenceItem]) -> List[SkillState]: ...

class IGapAnalyzer(Protocol):
    """Goal requirements - skill states; interest-vs-evidence conflict flags."""
    def analyze_gaps(self, goal: Goal, requirements: List[GoalRequirement], skill_states: List[SkillState]) -> List[Dict[str, Any]]: ...

class IPlanner(Protocol):
    """Candidate generation + constrained selection + scheduling."""
    def generate_plan(
        self,
        student: StudentProfile,
        goal: Goal,
        gaps: List[Dict[str, Any]],
        constraints: List[Constraint],
        preferences: List[Preference]
    ) -> Plan: ...

class IPlanValidator(Protocol):
    """Runs ALL checks on ANY plan (including LLM-proposed edits)."""
    def validate_plan(self, plan: Plan, student: StudentProfile) -> ValidationReport: ...

class IMasteryEvaluator(Protocol):
    """Distinguishes 'completed' from 'demonstrated proficiency'."""
    def evaluate_mastery(self, student_id: str, goal: Goal, criteria: MasteryCriteria, evidence: List[EvidenceItem]) -> Dict[str, Any]: ...

class IAdaptiveDiagnostic(Protocol):
    """Item selection + stop rule for short adaptive assessment."""
    def select_next_item(self, candidate_skills: List[str], previous_answers: List[Dict[str, Any]]) -> Optional[Exercise]: ...
    def is_complete(self, previous_answers: List[Dict[str, Any]]) -> bool: ...

