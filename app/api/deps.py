"""Shared FastAPI dependencies."""
from fastapi import HTTPException, Request

from app.services.onboarding_service import onboarding_service, StudentNotFoundError


def require_existing_student(request: Request) -> None:
    """
    Router-level guard for every route with a `{student_id}` path parameter.

    * Unknown ids get a 404 instead of a placeholder profile.
    * Real students (seed, database, persona roster) are loaded into memory first, so handlers that read
      `onboarding_service.students[...]` directly no longer answer "Student not found" for a seed student
      who simply has not been opened yet in this process.
    New students are created through POST /api/v2/students or POST /api/student/onboard.
    """
    student_id = request.path_params.get("student_id")
    if student_id is None:
        return
    try:
        onboarding_service.ensure_student_onboarded(student_id)
    except StudentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found. Create the profile first.")
