from typing import Dict, Any, List, Optional
from app.contracts.student import StudentProfile
from app.contracts.plan import PlanItem

class PersonaPolicy:
    """
    Default persona policy providing pluggable planner weights,
    conflict resolution rules, and advisory hooks.
    """
    enable_plan_adjustment: bool = False

    def __init__(self, spec: Dict[str, Any]):
        self.spec = spec
        self.weights = spec.get("planner_weights", {
            "cgpa_protection": 0.5,
            "skill_acceleration": 0.8,
            "workload_smoothing": 0.7
        })

    def adjust_plan_items(
        self,
        student: StudentProfile,
        items: List[PlanItem],
        gaps: Optional[List[Dict[str, Any]]] = None
    ) -> List[PlanItem]:
        """Hook to filter, reorder, or annotate plan items specifically for this persona."""
        return items

    def classify_requirement(
        self,
        course_id: Optional[str],
        slot_id: Optional[str],
        student: StudentProfile,
        default_is_required: bool
    ) -> bool:
        """
        Hook allowing a persona policy to classify an item as REQUIRED (locked core)
        or CHOOSABLE (elective/pool recommendation).
        """
        return default_is_required

    def get_advisories(self, student: StudentProfile) -> List[str]:
        """Persona-specific guidance or caution notes."""
        notes = []
        if (student.cgpa or 7.0) < 6.5 and self.weights.get("cgpa_protection", 0.5) > 0.6:
            notes.append("Prioritize core backlog clearance and CGPA stabilization before taking advanced electives.")
        return notes

class MBAPersonaPolicy(PersonaPolicy):
    """Core to MBA Pathway Policy."""
    def classify_requirement(
        self,
        course_id: Optional[str],
        slot_id: Optional[str],
        student: StudentProfile,
        default_is_required: bool
    ) -> bool:
        """Core to MBA requirement classification."""
        return default_is_required

class MTechPersonaPolicy(PersonaPolicy):
    """Core to M.Tech Higher Studies Pathway Policy."""
    def classify_requirement(
        self,
        course_id: Optional[str],
        slot_id: Optional[str],
        student: StudentProfile,
        default_is_required: bool
    ) -> bool:
        """Core to M.Tech requirement classification."""
        return default_is_required

