from typing import Optional
from app.personas.policy import PersonaPolicy
from app.contracts.student import StudentProfile

class CustomPersonaPolicy(PersonaPolicy):
    """Custom policy hooks for ee_power_core."""
    def classify_requirement(
        self,
        course_id: Optional[str],
        slot_id: Optional[str],
        student: StudentProfile,
        default_is_required: bool
    ) -> bool:
        """
        EE Power Core Persona requirement classification.
        Fixed degree core requirements remain locked; elective/breadth slots remain choosable.
        """
        return default_is_required
