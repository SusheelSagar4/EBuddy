import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.api.health import router as health_router
from app.api.ui_routes import router as ui_router
from app.api.student import router as student_router
from app.api.simulator import router as simulator_router
from app.api.admin import router as admin_router
from app.api.mba import router as mba_router

app = FastAPI(
    title="Adobe Personalised Learning Buddy",
    description="Adaptive academic planning and mastery buddy for IIT Bhubaneswar (B.Tech EE & B.Tech Metallurgical Engineering)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

# Include core routers
app.include_router(health_router, prefix="", tags=["System"])
app.include_router(ui_router)
app.include_router(student_router)
app.include_router(simulator_router)
app.include_router(admin_router)
app.include_router(mba_router)

# Ensure static directory exists and mount
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup Jinja2 Templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Mount web frontend (accessible at /legacy-web and /web)
web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
if os.path.exists(web_dir):
    app.mount("/legacy-web", StaticFiles(directory=web_dir, html=True), name="legacy_web")
    app.mount("/web", StaticFiles(directory=web_dir, html=True), name="web")


# -----------------------------------------------------------------------------
# 7 UI Shell Pages (Plain HTML + Vanilla JS + CSS / Jinja2)
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def page_home(request: Request):
    """Page 1: Home — Choose synthetic profile from dropdown, show academic summary."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"active_page": "home"}
    )

@app.get("/learn")
def page_learn():
    """Redirect to Daily Learning & Resources (Agent 2)."""
    return RedirectResponse(url="/legacy-web/#learn")

@app.get("/goals", response_class=HTMLResponse)
def page_goals(request: Request):
    """Page 2: Goal — Filter by student's branch plus cross-branch, Build roadmap."""
    return templates.TemplateResponse(
        request=request,
        name="goals.html",
        context={"active_page": "goals"}
    )

@app.get("/roadmap", response_class=HTMLResponse)
def page_roadmap(request: Request):
    """Page 3: Roadmap — Semester plan from deterministic planner, badges, warnings, version."""
    return templates.TemplateResponse(
        request=request,
        name="roadmap.html",
        context={"active_page": "roadmap"}
    )

@app.get("/diagnostic", response_class=HTMLResponse)
def page_diagnostic(request: Request):
    """Page 4: Diagnostic — CAT adaptive quiz (1 question at a time), progress, ability estimate."""
    return templates.TemplateResponse(
        request=request,
        name="diagnostic.html",
        context={"active_page": "diagnostic"}
    )

@app.get("/chat", response_class=HTMLResponse)
def page_chat(request: Request):
    """Page 5: Tutor Chat — IntentRouter -> Explainer via app/llm/client.py, clear LLM warning, cited KB codes."""
    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={"active_page": "chat"}
    )

@app.get("/approvals", response_class=HTMLResponse)
def page_approvals(request: Request):
    """Page 6: Approvals — List Agent 2-4 ChangeProposals, approve/reject triggers Agent 1 replanning."""
    return templates.TemplateResponse(
        request=request,
        name="approvals.html",
        context={"active_page": "approvals"}
    )

@app.get("/admin", response_class=HTMLResponse)
def page_admin(request: Request):
    """Page 7: Admin — Status panel, link to Adminer, read-only KB table viewer, reload seed."""
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={"active_page": "admin"}
    )

@app.get("/adminer")
def adminer_redirect():
    """Internal redirection to Adminer database viewer without hardcoding external host in templates."""
    return RedirectResponse(url=f"http://localhost:{settings.ADMINER_PORT}")
