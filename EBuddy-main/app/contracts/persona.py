from typing import List, Dict
from app.contracts.base import BaseContract

class PersonaSpec(BaseContract):
    persona_id: str
    goal_id: str
    description: str
    applicable_programmes: List[str]
    target_semester_range: List[int] = [1, 8]
    eligibility_notes: str = ""
    planner_weights: Dict[str, float] = {}
    status: str = 'draft_for_review'

