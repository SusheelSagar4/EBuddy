from typing import List
from app.contracts.student import StudentProfile
from app.personas.policy import PersonaPolicy


class CustomPersonaPolicy(PersonaPolicy):
    """Policy hooks for da_career: CGPA protection first, goal preparation second."""

    def get_advisories(self, student: StudentProfile) -> List[str]:
        notes = super().get_advisories(student)
        cgpa = student.cgpa if student.cgpa is not None else 7.0
        if student.backlogs > 0:
            notes.append(
                f"Active backlog(s): {student.backlogs}. Backlog clearance is scheduled first; Data Analyst Career Track preparation is limited "
                "to what fits after degree coursework inside your weekly-hours cap."
            )
        elif cgpa < 7.0:
            notes.append(
                f"CGPA {cgpa:.2f} is below 7.0. Many recruiters and programmes apply CGPA filters (exact cut-offs are not "
                "confirmed yet - check the official notices), so degree coursework keeps priority over Data Analyst Career Track preparation."
            )
        if student.current_semester >= 7:
            notes.append(
                "You are in the final year: the planner states which track phases fit before graduation at your weekly-hours "
                "cap and which do not, instead of compressing them silently."
            )
        return notes
