from typing import List, Dict, Optional
from app.contracts.base import BaseContract

class PersonaSpec(BaseContract):
    persona_id: str
    goal_id: str
    description: str
    applicable_programmes: List[str]
    target_semester_range: List[int] = [1, 8]
    eligibility_notes: str = ""
    planner_weights: Dict[str, float] = {}
    fallback_goals: Dict[str, str] = {}
    status: str = 'draft_for_review'
    # v1.4.0
    display_name: Optional[str] = None
    track_id: Optional[str] = None            # career track (sde / da / aiml) served by this persona
    additional_goal_ids: List[str] = []       # other goals this persona also serves (e.g. branch variants)

