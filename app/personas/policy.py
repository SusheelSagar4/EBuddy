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

    def get_advisories(self, student: StudentProfile) -> List[str]:
        """Persona-specific guidance or caution notes."""
        notes = []
        if (student.cgpa or 7.0) < 6.5 and self.weights.get("cgpa_protection", 0.5) > 0.6:
            notes.append("Prioritize core backlog clearance and CGPA stabilization before taking advanced electives.")
        return notes

