import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_health_endpoints():
    """Verify /health and /api/health return 200 and report system status."""
    r1 = client.get("/health")
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["status"] in ["healthy", "degraded"]
    assert "llm_configured" in d1

    r2 = client.get("/api/health")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["status"] in ["healthy", "degraded"]
    assert "database" in d2

def test_api_students():
    """Verify /api/students returns synthetic profiles from both EE and MME."""
    res = client.get("/api/students")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0
    student_ids = [s["student_id"] for s in data["students"]]
    # Must have both EE and MME profiles
    assert "CONF_STU_EE_POWER_01" in student_ids
    assert "CONF_STU_MME_PROCESS_01" in student_ids

def test_api_student_details():
    """Verify /api/students/{id} returns profile."""
    res = client.get("/api/students/CONF_STU_EE_POWER_01")
    assert res.status_code == 200
    data = res.json()
    assert data["student_id"] == "CONF_STU_EE_POWER_01"
    assert data["programme_id"] == "BTECH_EE"
    assert len(data["completed_courses"]) > 0

def test_api_goals_filtering():
    """Verify /api/goals filters by branch plus cross-branch goals."""
    # EE goals
    r_ee = client.get("/api/goals?programme_id=BTECH_EE")
    assert r_ee.status_code == 200
    d_ee = r_ee.json()
    ee_ids = [g["goal_id"] for g in d_ee["goals"]]
    assert "GOAL_EE_CORE_POWER" in ee_ids
    assert "GOAL_CROSS_SDE_DATA" in ee_ids # Cross-branch
    assert "GOAL_MM_PROCESS_ENGINEER" not in ee_ids

    # MME goals
    r_mm = client.get("/api/goals?programme_id=BTECH_MM")
    assert r_mm.status_code == 200
    d_mm = r_mm.json()
    mm_ids = [g["goal_id"] for g in d_mm["goals"]]
    assert "GOAL_MM_PROCESS_ENGINEER" in mm_ids
    assert "GOAL_CROSS_SDE_DATA" in mm_ids # Cross-branch
    assert "GOAL_EE_CORE_POWER" not in mm_ids

def test_api_roadmap_generate_ee_and_mme():
    """Verify deterministic roadmap generation for both EE and MME profiles."""
    # EE roadmap
    r_ee = client.post("/api/roadmap/generate", json={
        "student_id": "CONF_STU_EE_POWER_01",
        "goal_id": "GOAL_EE_CORE_POWER"
    })
    assert r_ee.status_code == 200
    d_ee = r_ee.json()
    assert d_ee["student_id"] == "CONF_STU_EE_POWER_01"
    assert d_ee["version"] >= 1
    assert len(d_ee["items"]) > 0
    # Every item must have KB code, title, credits, status
    assert "kb_code" in d_ee["items"][0]
    assert "status" in d_ee["items"][0]
    assert "credits" in d_ee["items"][0]

    # MME roadmap
    r_mm = client.post("/api/roadmap/generate", json={
        "student_id": "CONF_STU_MME_PROCESS_01",
        "goal_id": "GOAL_MM_PROCESS_ENGINEER"
    })
    assert r_mm.status_code == 200
    d_mm = r_mm.json()
    assert d_mm["student_id"] == "CONF_STU_MME_PROCESS_01"
    assert len(d_mm["items"]) > 0

def test_api_diagnostic_flow():
    """Verify adaptive diagnostic session initialization, question retrieval, and answer submission."""
    sid = "CONF_STU_EE_POWER_01"
    r_start = client.post("/api/diagnostic/start", json={"student_id": sid})
    assert r_start.status_code == 200

    r_next = client.get(f"/api/diagnostic/{sid}/next")
    assert r_next.status_code == 200
    d_next = r_next.json()
    assert "complete" in d_next
    if not d_next["complete"]:
        ex = d_next["exercise"]
        assert "exercise_id" in ex
        assert "options" in ex
        
        # Submit an answer
        r_ans = client.post(f"/api/diagnostic/{sid}/answer", json={
            "exercise_id": ex["exercise_id"],
            "skill_id": ex["skill_id"],
            "student_answer": ex["options"][0] if ex["options"] else "A"
        })
        assert r_ans.status_code == 200
        d_ans = r_ans.json()
        assert "score" in d_ans
        assert "is_correct" in d_ans
        assert "diagnostic_state" in d_ans

def test_api_chat_flow():
    """Verify tutor chat routing through IntentRouter -> Explainer with cited KB codes."""
    res = client.post("/api/chat", json={
        "student_id": "CONF_STU_EE_POWER_01",
        "message": "Why is EE3L004 on my roadmap?"
    })
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert "inferred_intent" in data
    assert "cited_kb_codes" in data
    assert len(data["cited_kb_codes"]) > 0

def test_api_proposals():
    """Verify pending proposals retrieval."""
    res = client.get("/api/proposals/CONF_STU_EE_POWER_01")
    assert res.status_code == 200
    data = res.json()
    assert "proposals" in data

def test_api_admin_endpoints():
    """Verify admin status, table listing, and table preview."""
    r_stat = client.get("/api/admin/status")
    assert r_stat.status_code == 200
    assert "db_healthy" in r_stat.json()

    r_tbls = client.get("/api/admin/tables")
    assert r_tbls.status_code == 200
    assert "kb.course" in r_tbls.json()["tables"]

    r_prev = client.get("/api/admin/tables/kb.course")
    assert r_prev.status_code == 200
    d_prev = r_prev.json()
    assert d_prev["count"] > 0
    assert "columns" in d_prev

def test_html_pages_render_successfully():
    """Verify all 7 UI Shell pages render valid HTML with 200 status."""
    routes = ["/", "/goals", "/roadmap", "/diagnostic", "/chat", "/approvals", "/admin"]
    for path in routes:
        res = client.get(path)
        assert res.status_code == 200, f"Page {path} returned status {res.status_code}"
        assert "SYNTHETIC PROFILE" in res.text
        assert "Personalised Learning Buddy" in res.text
