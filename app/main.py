from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from app.config import settings
from app.api.health import router as health_router
from app.api.student import router as student_router
from app.api.simulator import router as simulator_router
from app.api.admin import router as admin_router

app = FastAPI(
    title="Adobe Personalised Learning Buddy",
    description="Adaptive academic planning and mastery buddy for IIT Bhubaneswar (B.Tech EE & B.Tech Metallurgical Engineering)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

# Include core routers
app.include_router(health_router, prefix="", tags=["System"])
app.include_router(student_router)
app.include_router(simulator_router)
app.include_router(admin_router)

# Ensure static directory exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount web frontend shell
web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
if os.path.exists(web_dir):
    app.mount("/app", StaticFiles(directory=web_dir, html=True), name="web_app")

@app.get("/", response_class=HTMLResponse)
def root():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Personalised Learning Buddy - IIT Bhubaneswar</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; line-height: 1.6; background-color: #f8fafc; color: #0f172a; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 32px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }}
            h1 {{ color: #1e3a8a; margin-top: 0; }}
            .badge {{ display: inline-block; padding: 4px 10px; background: #e0e7ff; color: #3730a3; border-radius: 6px; font-weight: 600; font-size: 0.85rem; margin-bottom: 16px; }}
            .card {{ background: #f1f5f9; padding: 16px; border-radius: 8px; margin: 16px 0; border-left: 4px solid #3b82f6; }}
            .btn-cta {{ display: inline-block; background: #1e3a8a; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 12px 0; }}
            .btn-cta:hover {{ background: #172554; }}
            a {{ color: #2563eb; text-decoration: none; font-weight: 500; }}
            a:hover {{ text-decoration: underline; }}
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <span class="badge">Phase F Foundation Complete</span>
            <h1>Personalised Learning Buddy</h1>
            <p><strong>Target Institute:</strong> Indian Institute of Technology Bhubaneswar (IIT BBS)</p>
            <p><strong>Target Programmes:</strong> B.Tech Electrical Engineering & B.Tech Metallurgical and Materials Engineering</p>
            
            <div style="margin: 20px 0;">
                <a href="/app" class="btn-cta">🚀 Open Learning Buddy App (/app)</a>
            </div>

            <div class="card">
                <strong>System Health & Navigation:</strong>
                <ul>
                    <li><a href="/app">Interactive Web Application (/app)</a></li>
                    <li><a href="/health">Health & Seed Entity Status (/health)</a></li>
                    <li><a href="/docs">OpenAPI Documentation (/docs)</a></li>
                    <li><a href="http://localhost:{settings.ADMINER_PORT}" target="_blank">Adminer Database Viewer (:8080)</a></li>
                </ul>
            </div>

            <h3>Configured Gateway:</h3>
            <p>Model: <code>{settings.LLM_MODEL}</code> | Zero-Outbound Airgap: <strong>Enforced</strong></p>
        </div>
    </body>
    </html>
    """

