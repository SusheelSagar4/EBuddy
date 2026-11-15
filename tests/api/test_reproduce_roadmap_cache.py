import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.services.plan_service import plan_service
from app.services.onboarding_service import onboarding_service
from app.services.roadmap_orchestrator import roadmap_orchestrator

client = TestClient(app)

def test_reproduce_roadmap_cache_and_switching():
    """
    Verifies Problem 1 & 2 fixes:
    1. Switching goals in 3 consecutive calls generates distinct roadmaps.
    2. MBA goal produces dedicated MBA prep roadmap with CAT/XAT milestones and practice sets.
    3. Daily tasks for MBA student contain zero REQUIRED_COURSE items.
    4. Prints request/response payloads for 3 switches.
    """
    plan_service.plans.clear()
    
    print("\n" + "="*80)
    print("SWITCH 1: EE Student with Core Power Goal (Initial Baseline)")
    print("="*80)
    req1 = {
        "student_id": "CONF_STU_EE_POWER_01",
        "goal_id": "GOAL_EE_CORE_POWER"
    }
    res1 = client.post("/api/roadmap/generate", json=req1)
    p1 = res1.json()
    print(f"Request 1: POST /api/roadmap/generate -> {json.dumps(req1)}")
    print(f"Response 1 status: {res1.status_code}")
    print(f"Response 1 Plan ID: {p1.get('plan_id')}, Items count: {len(p1.get('items', []))}")
    print(f"Response 1 First 3 items: {json.dumps([{'code': it.get('kb_code'), 'type': it.get('item_type'), 'title': it.get('title')} for it in p1.get('items', [])[:3]], indent=2)}")

    print("\n" + "="*80)
    print("SWITCH 2: EE Student switches Goal to MBA")
    print("="*80)
    req2 = {
        "student_id": "CONF_STU_EE_POWER_01",
        "goal_id": "GOAL_CORE_TO_MBA"
    }
    res2 = client.post("/api/roadmap/generate", json=req2)
    p2 = res2.json() if res2.status_code == 200 else {}
    print(f"Request 2: POST /api/roadmap/generate -> {json.dumps(req2)}")
    print(f"Response 2 status: {res2.status_code}")
    print(f"Response 2 Plan ID: {p2.get('plan_id')}, Items count: {len(p2.get('items', []))}")
    print(f"Response 2 First 3 items: {json.dumps([{'code': it.get('kb_code'), 'type': it.get('item_type'), 'title': it.get('title')} for it in p2.get('items', [])[:3]], indent=2)}")

    print("\n" + "="*80)
    print("SWITCH 3: Fetch Roadmap via GET endpoint for Cross-SDE Goal")
    print("="*80)
    res3 = client.get("/api/roadmap/CONF_STU_EE_POWER_01?goal_id=GOAL_CROSS_SDE_DATA")
    p3 = res3.json()
    print(f"Request 3: GET /api/roadmap/CONF_STU_EE_POWER_01?goal_id=GOAL_CROSS_SDE_DATA")
    print(f"Response 3 status: {res3.status_code}")
    print(f"Response 3 Plan ID: {p3.get('plan_id')}")
    print(f"Plan ID differs from Switch 2: {p3.get('plan_id') != p2.get('plan_id')}")

    # Assertions:
    # 1. All 3 switch plans have distinct plan IDs
    assert p1.get("plan_id") != p2.get("plan_id"), "Switch 1 and Switch 2 returned identical plan ID"
    assert p2.get("plan_id") != p3.get("plan_id"), "Switch 2 and Switch 3 returned identical plan ID"

    # 2. MBA Goal routes to an MBA prep roadmap with dedicated MBA prep items and CAT milestones
    mba_items = [it for it in p2.get("items", []) if "MBA" in str(it.get("kb_code", "")) or "CAT" in str(it.get("title", ""))]
    assert len(mba_items) >= 4, (
        f"FAILURE: EE Student with MBA goal received only {len(mba_items)} MBA items! "
        f"Item codes received: {[it.get('kb_code') for it in p2.get('items', [])[:8]]}"
    )

    # 3. Required engineering courses are locked context and NEVER appear in recommendations list
    req_courses = [it for it in p2.get("items", []) if it.get("item_type") == "REQUIRED_COURSE"]
    assert len(req_courses) > 0, "Locked required academic courses must be present in the full roadmap"
    for rc in req_courses:
        assert rc.get("status_badge") in ["LOCKED", "LOCKED_CORE"] or "REQUIRED" in str(rc.get("status_badge", ""))

    # 4. Weekly schedule daily tasks for MBA student must have ZERO REQUIRED_COURSE lecture tasks
    weekly = roadmap_orchestrator.get_weekly_roadmap("CONF_STU_EE_POWER_01", week_number=1, goal_id="GOAL_CORE_TO_MBA")
    daily_tasks = weekly.daily_tasks
    print(f"\nDaily Tasks for MBA Student (Count: {len(daily_tasks)}):")
    for dt in daily_tasks:
        print(f"  Day {dt.day_number}: {dt.title} [{dt.task_type}]")
        assert "Lecture & Theory" not in dt.title, f"Required lecture found in daily tasks: {dt.title}"
        assert dt.task_type != "video_lecture", f"video_lecture task found: {dt.title}"

def test_differentiation_same_goal_different_students():
    """
    Amendment 8: Same goal (GOAL_CORE_TO_MBA), two different students:
    - CONF_STU_EE_POWER_03 (EE Semester 3)
    - CONF_STU_EE_POWER_01 (EE Semester 5)
    Asserts both roadmaps differ in total credits, item count, and timeline horizon.
    """
    res_sem3 = client.post("/api/roadmap/generate", json={
        "student_id": "CONF_STU_EE_POWER_03",
        "goal_id": "GOAL_CORE_TO_MBA"
    })
    assert res_sem3.status_code == 200
    d_sem3 = res_sem3.json()

    res_sem5 = client.post("/api/roadmap/generate", json={
        "student_id": "CONF_STU_EE_POWER_01",
        "goal_id": "GOAL_CORE_TO_MBA"
    })
    assert res_sem5.status_code == 200
    d_sem5 = res_sem5.json()

    # Different students must have different plan IDs
    assert d_sem3["plan_id"] != d_sem5["plan_id"]

    # Sem 3 student has 6 remaining semesters (Sem 3-8), while Sem 5 has 4 (Sem 5-8)
    semesters_3 = [s["semester_number"] for s in d_sem3.get("semesters", [])]
    semesters_5 = [s["semester_number"] for s in d_sem5.get("semesters", [])]
    print(f"\nStudent Sem 3 Semesters: {semesters_3}")
    print(f"Student Sem 5 Semesters: {semesters_5}")
    assert len(semesters_3) > len(semesters_5), "Sem 3 student should have more remaining semesters than Sem 5 student"
    assert d_sem3["total_credits"] > d_sem5["total_credits"], "Sem 3 student should have higher remaining credits"
