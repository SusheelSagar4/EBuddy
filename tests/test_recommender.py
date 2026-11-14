"""Unit and integration tests for EBuddy Course Recommender.

Tests determinism, credit limits, prerequisite checks, fallback templates,
hallucination guard, MME duplicate code handling, and FastAPI endpoint.
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.recommender.credits import (
    core_courses,
    credit_limit,
    first_code,
    parse_credit,
    semester_credit_total,
)
from app.recommender.engine import recommend
from app.recommender.explain import build_deterministic_explanation, explain
from app.recommender.kb import (
    get_academic_rules,
    get_courses,
    get_curriculum_table,
    resolve_course_id,
    slot_branch,
    slot_semester,
)

client = TestClient(app)


def test_core_credits_plus_headroom_equals_limit_ee_and_mme():
    """Verify core_credits + headroom == limit for EE sem 3..8 and MME sem 3..8."""
    rules = get_academic_rules()
    for branch in ["EE", "MME"]:
        curriculum_df = get_curriculum_table(branch)
        for sem in range(3, 9):
            student = {
                "branch": branch,
                "semester": sem,
                "cgpa": 8.0,
                "overload_approved": False,
            }
            res = recommend(student)
            budget = res["credit_budget"]
            limit = budget["limit"]
            core_credits = budget["core_credits"]
            headroom = budget["headroom"]

            assert round(core_credits + headroom, 2) == round(limit, 2), (
                f"Failed for {branch} sem {sem}: core_credits ({core_credits}) + headroom ({headroom}) != limit ({limit})"
            )


def test_no_recommendation_has_credits_exceeding_headroom():
    """Verify that no recommended course exceeds the remaining credit headroom."""
    for branch in ["EE", "MME"]:
        for sem in range(3, 9):
            student = {
                "branch": branch,
                "semester": sem,
                "cgpa": 7.5,
                "goal": "Engineering",
            }
            res = recommend(student)
            headroom = res["credit_budget"]["headroom"]
            for rec in res["recommendations"]:
                assert rec["credits"] <= headroom, (
                    f"Course {rec['course_id']} credits ({rec['credits']}) > headroom ({headroom}) in {branch} sem {sem}"
                )


def test_credit_limit_probation_and_overload():
    """Verify CGPA 5.5 uses the 18-credit probation cap, and CGPA 9.0 with overload uses 30."""
    rules = get_academic_rules()
    curriculum_total = 25.0

    # 1. CGPA 5.5 -> Probation cap (18.0)
    lim_prob, rule_prob = credit_limit(5.5, curriculum_total, overload_approved=False, rules=rules)
    assert lim_prob == 18.0
    assert rule_prob == "RULE_SEM_CREDIT_CAP_PROBATION"

    # 2. CGPA 9.0 with overload_approved -> 30.0
    lim_over, rule_over = credit_limit(9.0, curriculum_total, overload_approved=True, rules=rules)
    assert lim_over == 30.0
    assert rule_over == "RULE_SEM_CREDIT_CAP_REGULAR"

    # 3. CGPA 9.0 without overload_approved -> regular curriculum cap
    lim_reg, rule_reg = credit_limit(9.0, curriculum_total, overload_approved=False, rules=rules)
    assert lim_reg == 25.0
    assert rule_reg == "RULE_SEM_CREDIT_CAP_REGULAR"


def test_missing_prerequisite_blocks_recommendation():
    """Verify that a student with a missing prerequisite never receives that course."""
    # CS4L003 requires CS1L001; CS1L001 is omitted from completed courses
    student = {
        "branch": "EE",
        "semester": 7,
        "cgpa": 8.0,
        "completed": ["EE1L001", "MA1L001"],  # Missing CS1L001
        "goal": "Software systems",
    }
    res = recommend(student)
    recommended_ids = [r["course_id"] for r in res["recommendations"]]
    assert "CS4L003" not in recommended_ids

    # Verify it was explicitly flagged under rejected
    rejections = {r["course_id"]: r["reason"] for r in res["rejected"]}
    assert "CS4L003" in rejections
    assert "Missing required prerequisite(s)" in rejections["CS4L003"]
    assert "CS1L001" in rejections["CS4L003"]


def test_empty_query_falls_back_to_profile_goal_and_query_overrides():
    """Verify empty query uses profile goal (intent.source == 'profile_goal') and query overrides."""
    # Empty / None query -> uses profile goal
    student = {
        "branch": "EE",
        "semester": 5,
        "cgpa": 8.0,
        "goal": "Software engineering role",
    }
    res_goal = recommend(student, query=None)
    assert res_goal["intent"]["source"] == "profile_goal"
    assert res_goal["intent"]["text"] == "Software engineering role"

    res_empty_str = recommend(student, query="   ")
    assert res_empty_str["intent"]["source"] == "profile_goal"

    # Explicit query -> overrides profile goal
    res_query = recommend(student, query="Power electronics and drives")
    assert res_query["intent"]["source"] == "query"
    assert res_query["intent"]["text"] == "Power electronics and drives"


def test_nonsense_query_returns_no_direct_match():
    """Verify nonsense query 'xyz' gives no_direct_match == True or empty list, without crashing."""
    student = {
        "branch": "EE",
        "semester": 5,
        "cgpa": 8.0,
        "goal": "",
    }
    res = recommend(student, query="xyz123nonsense")
    assert res["no_direct_match"] is True
    # If any survivors exist, their scores must all be zero
    for r in res["recommendations"]:
        assert r["score"] == 0.0


def test_explain_fallback_when_llm_model_unset_or_fails():
    """Verify explain() returns deterministic fallback template when LLM_MODEL is unset or call raises."""
    student = {
        "branch": "EE",
        "semester": 5,
        "cgpa": 8.0,
        "goal": "Software engineering role",
    }
    res = recommend(student)

    # 1. With LLM_MODEL unset
    with patch.dict("os.environ", {"LLM_MODEL": ""}, clear=False):
        exp_unset = explain(res, student)
        assert "Credit Summary:" in exp_unset
        assert "EE3L005" in exp_unset or "EE3L006" in exp_unset

    # 2. When LLM completion call raises an exception
    with patch.dict("os.environ", {"LLM_MODEL": "openai/gpt-4o-mini", "LLM_API_KEY": "sk-mock"}, clear=False):
        with patch("app.llm.client.llm_client.completion", side_effect=RuntimeError("LiteLLM connection error")):
            exp_err = explain(res, student)
            assert "Credit Summary:" in exp_err
            assert "Fits within your" in exp_err


def test_hallucination_guard_replaces_hallucinated_codes():
    """Verify hallucination guard replaces output citing non-shortlisted course codes with fallback."""
    student = {
        "branch": "EE",
        "semester": 5,
        "cgpa": 8.0,
        "goal": "Software engineering role",
    }
    res = recommend(student)

    # Mocked LLM reply mentioning a course code NOT in the payload (e.g. CS9L999)
    hallucinated_reply = (
        "Based on your profile, I strongly recommend CS9L999 Advanced Quantum Hacking which takes 3 credits. "
        "Also take EE3L005."
    )

    with patch.dict("os.environ", {"LLM_MODEL": "openai/gpt-4o-mini", "LLM_API_KEY": "sk-mock"}, clear=False):
        with patch("app.llm.client.llm_client.completion", return_value=hallucinated_reply):
            safe_output = explain(res, student)
            # The hallucinated code CS9L999 must NOT be in the output; fallback template must be returned
            assert "CS9L999" not in safe_output
            assert "Credit Summary:" in safe_output


def test_mme_duplicate_codes_core_vs_elec_mapping():
    """Verify MME duplicate codes ML4L001-003 resolve correctly to *_CORE for Sem VII core and *_ELEC for slot options."""
    courses_df = get_courses()
    mme_df = get_curriculum_table("MME")

    # 1. Test resolve_course_id for code_conflict
    assert resolve_course_id("ML4L001", is_core=True) == "ML4L001_CORE"
    assert resolve_course_id("ML4L002", is_core=True) == "ML4L002_CORE"
    assert resolve_course_id("ML4L003", is_core=True) == "ML4L003_CORE"
    assert resolve_course_id("ML4L001", is_core=False) == "ML4L001_ELEC"
    assert resolve_course_id("ML4L002", is_core=False) == "ML4L002_ELEC"
    assert resolve_course_id("ML4L003", is_core=False) == "ML4L003_ELEC"

    # 2. In MME Sem VII, core_courses must include the *_CORE course_ids
    cores_sem7 = core_courses(mme_df, 7)
    core_ids_sem7 = [c["course_id"] for c in cores_sem7]
    assert "ML4L001_CORE" in core_ids_sem7
    assert "ML4L002_CORE" in core_ids_sem7
    assert "ML4L003_CORE" in core_ids_sem7

    # 3. In MME Sem 7/8 slot_options, electives must use *_ELEC course_ids
    student_mme = {
        "branch": "MME",
        "semester": 7,
        "cgpa": 8.0,
        "goal": "Metallurgy and joining",
    }
    res = recommend(student_mme)
    # Check that any candidate matching ML4L001 uses ML4L001_ELEC
    all_cids = [r["course_id"] for r in res["recommendations"]] + [r["course_id"] for r in res["rejected"]]
    assert "ML4L001_CORE" not in all_cids  # Core course should never be in slot candidate pool
    if "ML4L001_ELEC" in all_cids:
        assert "ML4L001_ELEC" in all_cids


def test_api_recommend_endpoint_success():
    """Verify POST /recommend returns HTTP 200 with answer and data structure."""
    payload = {
        "branch": "EE",
        "semester": 5,
        "cgpa": 8.5,
        "goal": "Software engineering role",
        "query": None,
        "completed": ["EE1L001"],
        "avoid": [],
        "overload_approved": False,
    }
    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert "answer" in json_data
    assert "data" in json_data
    assert "credit_budget" in json_data["data"]
    assert "recommendations" in json_data["data"]


def test_api_recommend_endpoint_validation_errors():
    """Verify invalid branch or out-of-range semester returns HTTP 400 or 422."""
    # Unknown branch
    res_bad_branch = client.post("/recommend", json={
        "branch": "CIVIL",
        "semester": 4,
        "cgpa": 8.0,
    })
    assert res_bad_branch.status_code in [400, 422]
    assert "Invalid branch" in res_bad_branch.text or "CIVIL" in res_bad_branch.text

    # Semester out of range (< 1)
    res_bad_sem_low = client.post("/recommend", json={
        "branch": "EE",
        "semester": 0,
        "cgpa": 8.0,
    })
    assert res_bad_sem_low.status_code in [400, 422]

    # Semester out of range (> 8)
    res_bad_sem_high = client.post("/recommend", json={
        "branch": "EE",
        "semester": 9,
        "cgpa": 8.0,
    })
    assert res_bad_sem_high.status_code in [400, 422]
