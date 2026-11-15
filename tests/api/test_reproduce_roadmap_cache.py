import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.services.plan_service import plan_service
from app.services.onboarding_service import onboarding_service

client = TestClient(app)

@pytest.mark.xfail(reason="Step A reproduction test proving Problem 1 & 2 - resolved in Step C-F", strict=False)
def test_reproduce_roadmap_cache_and_switching():
    """
    Reproduction test for Problem 1 & 2:
    1. Requests roadmap for (EE student, goal MBA) and (MME student, goal metallurgy).
    2. Demonstrates that EE student with MBA goal gets generic EE courses instead of MBA prep.
    3. Demonstrates that switching goal on GET /api/roadmap/{student_id} ignores goal_id and returns stale cached plan.
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
    print("SWITCH 2: EE Student switches Goal to MBA (Problem 1: MBA Routing & Daily Tasks)")
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
    print("SWITCH 3: Fetch Roadmap via GET endpoint (Problem 2: UI Switch & Cache Ignored)")
    print("="*80)
    # The frontend calls GET /api/roadmap/{student_id}.
    # Even if query param ?goal_id=GOAL_CROSS_SDE_DATA is passed, GET endpoint ignores it and returns the cached plan!
    res3 = client.get("/api/roadmap/CONF_STU_EE_POWER_01?goal_id=GOAL_CROSS_SDE_DATA")
    p3 = res3.json()
    print(f"Request 3: GET /api/roadmap/CONF_STU_EE_POWER_01?goal_id=GOAL_CROSS_SDE_DATA")
    print(f"Response 3 status: {res3.status_code}")
    print(f"Response 3 Plan ID: {p3.get('plan_id')}")
    print(f"Plan ID matches Switch 2: {p3.get('plan_id') == p2.get('plan_id')}")

    # Assertion 1: MBA Goal must route to an MBA prep roadmap, NOT generic EE course planner
    mba_items = [it for it in p2.get("items", []) if "MBA" in str(it.get("kb_code", "")) or "CAT" in str(it.get("title", ""))]
    assert len(mba_items) > 0, (
        f"FAILURE: EE Student with MBA goal received generic EE engineering courses! "
        f"Item codes received: {[it.get('kb_code') for it in p2.get('items', [])[:6]]}"
    )
