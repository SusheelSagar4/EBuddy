from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum
from app.contracts.base import BaseContract

class Intent(str, Enum):
    PLAN_QUERY = "plan_query"
    PLAN_EDIT = "plan_edit"
    WEEK_EXCEPTION = "week_exception"
    DOMAIN_CONCEPT = "domain_concept"
    GOAL_CHANGE = "goal_change"
    DIAGNOSTIC_REQUEST = "diagnostic_request"
    PROGRESS_CHECK = "progress_check"
    CLARIFICATION = "clarification"
    OFF_TOPIC = "off_topic"

class ContextCard(BaseContract):
    student_id: str
    programme_id: str
    current_semester: int
    cgpa: Optional[float] = None
    goal_id: str
    goal_name: str
    skill_gaps: List[Dict[str, Any]]
    current_plan_items: List[Dict[str, Any]]
    verified_facts: List[Dict[str, Any]]
    unverified_advisories: List[Dict[str, Any]]
    long_term_memory: Optional[str] = None
    disclaimer: str = (
        "Strict Guardrail: The buddy never states dates, cut-offs, fees or credit limits "
        "unless verified in official institutional records; otherwise it states 'not confirmed yet' "
        "and directs the student to the official IIT Bhubaneswar administration."
    )

class ChatTurn(BaseContract):
    turn_id: str
    student_id: str
    user_message: str
    inferred_intent: Intent
    context_card: ContextCard
    model_response: str
    plan_affected: bool = False
    created_at: datetime

class Explanation(BaseContract):
    subject: str
    audience: str = 'student'
    short_summary: str
    detailed_rationale: str
    citations: List[str] = []

