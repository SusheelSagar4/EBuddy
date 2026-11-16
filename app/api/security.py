"""
Optional protection for administrative endpoints.

When the ADMIN_TOKEN environment variable is set, every state-changing request (POST, PUT, PATCH,
DELETE) to an admin route must carry the same value in the `X-Admin-Token` header. Read-only
requests stay open so the dashboards keep working. When ADMIN_TOKEN is empty (the default for the
local demo) nothing is enforced, so `docker compose up` and the test-suite behave as before.
"""
import hmac
import os
from typing import Optional

from fastapi import Header, HTTPException, Request

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def configured_admin_token() -> str:
    """Read at request time so the token can be changed without re-importing the app."""
    token = os.getenv("ADMIN_TOKEN")
    if token is None:
        try:
            from app.config import settings
            token = settings.ADMIN_TOKEN or ""
        except Exception:
            token = ""
    return token.strip()


def require_admin_token(request: Request, x_admin_token: Optional[str] = Header(default=None)) -> None:
    expected = configured_admin_token()
    if not expected or request.method.upper() in _SAFE_METHODS:
        return
    supplied = (x_admin_token or "").strip()
    if not supplied or not hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Admin token required: send the ADMIN_TOKEN value in the X-Admin-Token header.")
