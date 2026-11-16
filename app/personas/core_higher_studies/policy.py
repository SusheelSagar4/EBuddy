from typing import List
from app.contracts.student import StudentProfile
from app.personas.policy import PersonaPolicy


class CustomPersonaPolicy(PersonaPolicy):
    """Policy hooks for core_higher_studies: CGPA protection first, goal preparation second."""

    def get_advisories(self, student: StudentProfile) -> List[str]:
        notes = super().get_advisories(student)
        cgpa = student.cgpa if student.cgpa is not None else 7.0
        if student.backlogs > 0:
            notes.append(
                f"Active backlog(s): {student.backlogs}. Backlog clearance is scheduled first; Higher Studies (M.Tech / MS / PhD) preparation is limited "
                "to what fits after degree coursework inside your weekly-hours cap."
            )
        elif cgpa < 7.0:
            notes.append(
                f"CGPA {cgpa:.2f} is below 7.0. Many recruiters and programmes apply CGPA filters (exact cut-offs are not "
                "confirmed yet - check the official notices), so degree coursework keeps priority over Higher Studies (M.Tech / MS / PhD) preparation."
            )
        return notes
