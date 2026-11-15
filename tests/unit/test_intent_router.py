import pytest
from app.llm.tasks.intent_router import intent_router
from app.kb.repositories import GoalRepo

goal_repo = GoalRepo()
valid_ids = {g.goal_id for g in goal_repo.list_all()}

def test_intent_router_mba_goal():
    res = intent_router.route_goal_text("I want to do MBA and crack CAT exam", programme_id="BTECH_EE")
    assert res.goal_id == "GOAL_CORE_TO_MBA"
    assert res.confidence >= 0.8
    assert "Is that right?" in res.confirmation_sentence
    assert "MBA" in res.goal_name
    assert res.goal_id in valid_ids
    for alt in res.alternatives:
        assert alt.goal_id in valid_ids

def test_intent_router_core_company_ee_and_mm():
    # EE core
    res_ee = intent_router.route_goal_text("placement in a core company", programme_id="BTECH_EE")
    assert res_ee.goal_id in ["GOAL_EE_CORE_POWER", "GOAL_EE_CORE_VLSI"]
    assert res_ee.goal_id in valid_ids
    assert "Is that right?" in res_ee.confirmation_sentence

    # MM core
    res_mm = intent_router.route_goal_text("placement in a core company", programme_id="BTECH_MM")
    assert res_mm.goal_id in ["GOAL_MM_PROCESS_ENGINEER", "GOAL_MM_ADVANCED_MATERIALS"]
    assert res_mm.goal_id in valid_ids

def test_intent_router_nonsense_query():
    res = intent_router.route_goal_text("asdlkfjasd098234-xyz-nonsense", programme_id="BTECH_EE")
    # Low confidence, but returns a valid candidate and alternatives
    assert res.confidence <= 0.35
    assert res.goal_id in valid_ids
    assert len(res.alternatives) > 0
    assert "Is that right?" in res.confirmation_sentence

def test_intent_router_upsc_and_startup():
    res_upsc = intent_router.route_goal_text("I want to clear civil services UPSC CSE exam", programme_id="BTECH_EE")
    assert res_upsc.goal_id == "GOAL_UPSC_CSE"
    assert res_upsc.goal_id in valid_ids

    res_startup = intent_router.route_goal_text("build my deep-tech hardware startup venture", programme_id="BTECH_EE")
    assert res_startup.goal_id == "GOAL_STARTUP_FOUNDER"
    assert res_startup.goal_id in valid_ids
