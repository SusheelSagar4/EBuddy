"""Validation shared by the two profile-creation routes (POST /api/v2/students and POST /api/student/onboard)."""
import re
from typing import Iterable, List, Optional

from fastapi import HTTPException

from app.services.onboarding_service import onboarding_service
from app.kb.course_notes import course_notes

STUDENT_ID = re.compile(r"[A-Za-z0-9_-]{3,40}")
PROGRAMMES = {"BTECH_EE", "BTECH_MM"}


def validate_new_profile(student_id: str, name: Optional[str], programme_id: str, current_semester: int,
                         cgpa: Optional[float], backlogs: int, goal_id: Optional[str],
                         completed_course_ids: Optional[Iterable[str]], known_courses,
                         weekly_hours_cap: Optional[float] = None, credit_cap: Optional[float] = None) -> str:
    """Raises 400 / 409 for an invalid or already-existing profile; returns the cleaned student id."""
    sid = (student_id or "").strip()
    if not STUDENT_ID.fullmatch(sid):
        raise HTTPException(status_code=400, detail="student_id must be 3-40 characters: letters, digits, '_' or '-'.")
    # Never overwrite an existing profile: seed, database, persona roster or created earlier in this process.
    if onboarding_service.student_exists(sid):
        raise HTTPException(status_code=409, detail=f"Student {sid} already exists; choose another student_id.")
    if programme_id not in PROGRAMMES:
        raise HTTPException(status_code=400, detail=f"programme_id must be one of {sorted(PROGRAMMES)}")
    if not 1 <= current_semester <= 8:
        raise HTTPException(status_code=400, detail="current_semester must be between 1 and 8")
    if cgpa is not None and not 0 <= cgpa <= 10:
        raise HTTPException(status_code=400, detail="cgpa must be between 0 and 10")
    if backlogs < 0:
        raise HTTPException(status_code=400, detail="backlogs cannot be negative")
    if weekly_hours_cap is not None and not 0 < weekly_hours_cap <= 100:
        raise HTTPException(status_code=400, detail="weekly_hours_cap must be between 0 and 100")
    if credit_cap is not None and not 0 < credit_cap <= 40:
        raise HTTPException(status_code=400, detail="credit_cap must be between 0 and 40")
    if not (name or "").strip():
        raise HTTPException(status_code=400, detail="name is required")
    if len(name or "") > 120:
        raise HTTPException(status_code=400, detail="name must be at most 120 characters")
    if goal_id is not None and onboarding_service.goal_repo.get_by_id(goal_id) is None:
        raise HTTPException(status_code=400, detail=f"Unknown goal {goal_id}")
    resolve_course_codes(completed_course_ids, known_courses)  # raises 400 for unknown / ambiguous codes
    return sid


def resolve_course_codes(codes: Optional[Iterable[str]], known_courses) -> List[str]:
    """
    Maps what a student typed (printed code, internal id or a known alternative name/code) to internal course ids.
    A printed code is not unique (ML4L001 is both a Sem VII core course and an elective), so an ambiguous code is
    refused with the options instead of picking one silently.
    """
    resolved, unknown, ambiguous = [], [], []
    for raw in codes or []:
        ids = [cid for cid in course_notes.resolve(raw) if cid in known_courses]
        if not ids:
            unknown.append(raw)
        elif len(ids) > 1:
            ambiguous.append(f"{raw} is used for {' and for '.join(course_notes.describe(i) + ' (id ' + i + ')' for i in ids)}")
        elif ids[0] not in resolved:
            resolved.append(ids[0])
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown course code(s): {', '.join(unknown)}. Use codes from the catalogue.")
    if ambiguous:
        raise HTTPException(status_code=400, detail=("The official curriculum uses the same code for two different courses: "
                                                     + "; ".join(ambiguous) + ". Give the course id instead."))
    return resolved
