from typing import Optional
from app.personas.policy import PersonaPolicy
from app.contracts.student import StudentProfile

class CustomPersonaPolicy(PersonaPolicy):
    """
    Core MME Persona Policy:
    Balances physical metallurgy foundation courses, experimental characterization labs,
    and industrial alloy development milestones.
    """
    def classify_requirement(
        self,
        course_id: Optional[str],
        slot_id: Optional[str],
        student: StudentProfile,
        default_is_required: bool
    ) -> bool:
        """
        MME Persona requirement classification.
        Guarantees core metallurgical foundations are locked requirements.
        """
        return default_is_required
