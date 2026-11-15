"""Unit and integration tests for EBuddy Course Recommender.

Tests determinism, credit limits, prerequisite checks, fallback templates,
hallucination guard, MME duplicate code handling, multi-slot credit budgets,
future elective options, relevance honesty, and FastAPI endpoint with LLM visibility.
"""

import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.recommender.api import RecommendRequest, get_recommendations
from app.recommender.credits import (
    core_courses,
    credit_limit,
    first_code,
    open_slot_info,
    parse_credit,
    semester_credit_total,
)
from app.recommender.engine import MIN_RELEVANCE, recommend
from app.recommender.explain import build_deterministic_explanation, explain
from app.recommender.kb import (
    get_academic_rules,
    get_courses,
    get_curriculum_table,
    resolve_course_id,
    slot_branch,
    slot_semester,
)
from app.recommender.retrieval import STOPWORDS, intent_terms, score_courses


def test_core_credits_plus_headroom_equals_limit_ee_and_mme():
    """Verify core_credits + headroom == limit for EE sem 3..8 and MME sem 3..8."""
    for branch in ["EE", "MME"]:
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
    # CS4L003 requires CS1L001; explicit backlog on CS1L001 removes it from completed
    student = {
        "branch": "EE",
        "semester": 7,
        "cgpa": 8.0,
        "backlogs": ["CS1L001"],
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
    """Verify empty query uses profile goal and explicit query overrides."""
    student = {
        "branch": "EE",
        "semester": 5,
        "cgpa": 8.0,
        "goal": "Software engineering role",
    }
    res_goal = recommend(student, query=None)
    assert res_goal["intent"]["source"] == "profile_goal"
    assert res_goal["intent"]["query_had_topic"] is False
    assert res_goal["intent"]["text"] == "Software engineering role"

    res_empty_str = recommend(student, query="   ")
    assert res_empty_str["intent"]["source"] == "profile_goal"
    assert res_empty_str["intent"]["query_had_topic"] is False

    res_query = recommend(student, query="Power electronics and drives")
    assert res_query["intent"]["source"] == "query"
    assert res_query["intent"]["query_had_topic"] is True
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
    assert res["weak_match"] is True
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
        exp_unset, llm_used, llm_err = explain(res, student)
        assert llm_used is False
        assert llm_err == "LLM_MODEL not configured"
        assert "Credit Summary:" in exp_unset
        assert "EE3L005" in exp_unset or "EE3L006" in exp_unset

    # 2. When LLM completion call raises an exception
    with patch.dict("os.environ", {"LLM_MODEL": "openai/gpt-4o-mini", "LLM_API_KEY": "sk-mock"}, clear=False):
        with patch("app.llm.client.llm_client.completion", side_effect=RuntimeError("LiteLLM connection error")):
            exp_err, llm_used, llm_err = explain(res, student)
            assert llm_used is False
            assert "RuntimeError" in (llm_err or "")
            assert "Credit Summary:" in exp_err


def test_hallucination_guard_replaces_hallucinated_codes():
    """Verify hallucination guard replaces output citing non-shortlisted course codes with fallback."""
    student = {
        "branch": "EE",
        "semester": 5,
        "cgpa": 8.0,
        "goal": "Software engineering role",
    }
    res = recommend(student)

    hallucinated_reply = (
        "Based on your profile, I strongly recommend CS9L999 Advanced Quantum Hacking which takes 3 credits. "
        "Also take EE3L005."
    )

    with patch.dict("os.environ", {"LLM_MODEL": "openai/gpt-4o-mini", "LLM_API_KEY": "sk-mock"}, clear=False):
        with patch("app.llm.client.llm_client.completion", return_value=hallucinated_reply):
            safe_output, llm_used, llm_err = explain(res, student)
            assert llm_used is False
            assert "CS9L999" in (llm_err or "")
            assert "CS9L999" not in safe_output
            assert "Credit Summary:" in safe_output


def test_mme_duplicate_codes_core_vs_elec_mapping():
    """Verify MME duplicate codes ML4L001-003 resolve correctly to *_CORE for Sem VII core and *_ELEC for slot options."""
    mme_df = get_curriculum_table("MME")

    assert resolve_course_id("ML4L001", is_core=True) == "ML4L001_CORE"
    assert resolve_course_id("ML4L002", is_core=True) == "ML4L002_CORE"
    assert resolve_course_id("ML4L003", is_core=True) == "ML4L003_CORE"
    assert resolve_course_id("ML4L001", is_core=False) == "ML4L001_ELEC"
    assert resolve_course_id("ML4L002", is_core=False) == "ML4L002_ELEC"
    assert resolve_course_id("ML4L003", is_core=False) == "ML4L003_ELEC"

    cores_sem7 = core_courses(mme_df, 7)
    core_ids_sem7 = [c["course_id"] for c in cores_sem7]
    assert "ML4L001_CORE" in core_ids_sem7
    assert "ML4L002_CORE" in core_ids_sem7
    assert "ML4L003_CORE" in core_ids_sem7

    student_mme = {
        "branch": "MME",
        "semester": 7,
        "cgpa": 8.0,
        "goal": "Metallurgy and joining",
    }
    res = recommend(student_mme)
    all_cids = [r["course_id"] for r in res["recommendations"]] + [r["course_id"] for r in res["rejected"]]
    assert "ML4L001_CORE" not in all_cids


def test_deterministic_identical_output_for_same_input():
    """Verify the recommendation engine returns strictly identical results when run twice with same input."""
    student = {
        "branch": "EE",
        "semester": 6,
        "cgpa": 8.2,
        "goal": "VLSI design and embedded systems",
        "avoid": [],
    }
    res1 = recommend(student, query="embedded chip design")
    res2 = recommend(student, query="embedded chip design")

    assert res1 == res2
    assert res1["recommendations"] == res2["recommendations"]


def test_unmapped_course_scoring_comparable():
    """Verify unmapped course CS4L003 scores > 0.5 for software engineering role and is comparable to mapped courses."""
    terms = intent_terms("Software engineering role")
    scored = score_courses(["CS4L003", "CS6L001"], terms)

    cs4_score = scored["CS4L003"]["score"]
    cs6_score = scored["CS6L001"]["score"]

    assert cs4_score > 0.5, f"Expected CS4L003 score > 0.5, got {cs4_score}"
    assert cs6_score > 0.5, f"Expected CS6L001 score > 0.5, got {cs6_score}"
    assert abs(cs6_score - cs4_score) < 0.35, "Mapped and unmapped scores should be comparable"


# ==============================================================================
# NEW REQUIREMENT TESTS (Phase G Items 1 - 8)
# ==============================================================================

def test_intent_fallback_generic_query_uses_profile_goal():
    """Item 1: Query without topic words falls back to profile goal with query_had_topic=False."""
    student = {
        "branch": "EE",
        "semester": 7,
        "cgpa": 8.0,
        "goal": "Software engineering role",
    }
    # Generic query with no topical content
    query = "what course should I take this semester"
    res = recommend(student, query=query)

    assert res["intent"]["source"] == "profile_goal"
    assert res["intent"]["query_had_topic"] is False
    assert len(res["intent"]["terms"]) > 0

    recs_map = {r["course_id"]: r["score"] for r in res["recommendations"]}
    assert "CS4L003" in recs_map
    assert "CS6L001" in recs_map
    assert recs_map["CS4L003"] > 0
    assert recs_map["CS6L001"] > 0


def test_completed_courses_union_and_backlogs():
    """Item 3: Completed = earlier core UNION explicit, minus backlogs."""
    # In EE Sem 7, CS1L001 was core in Sem 2.
    # Case A: Short explicit list ["EE1L001"] must not disable inference of CS1L001
    student_a = {
        "branch": "EE",
        "semester": 7,
        "cgpa": 8.0,
        "completed": ["EE1L001"],
        "goal": "Software engineering role",
    }
    res_a = recommend(student_a)
    recs_a = [r["course_id"] for r in res_a["recommendations"]]
    assert "CS4L003" in recs_a  # CS1L001 inferred as completed, so CS4L003 eligible

    # Case B: CS1L001 in backlogs must disable prerequisite clearance
    student_b = {
        "branch": "EE",
        "semester": 7,
        "cgpa": 8.0,
        "completed": ["EE1L001"],
        "backlogs": ["CS1L001"],
        "goal": "Software engineering role",
    }
    res_b = recommend(student_b)
    recs_b = [r["course_id"] for r in res_b["recommendations"]]
    assert "CS4L003" not in recs_b
    rej_b = {r["course_id"]: r["reason"] for r in res_b["rejected"]}
    assert "CS4L003" in rej_b
    assert "CS1L001" in rej_b["CS4L003"]


def test_relevance_honesty_and_generic_stoplist():
    """Item 4: MIN_RELEVANCE = 0.2 and weak_match flag, stoplist filters noise words."""
    assert MIN_RELEVANCE == 0.2
    for word in ["system", "systems", "engineering", "technology", "design", "analysis", "introduction", "advanced"]:
        assert word in STOPWORDS

    # When query has terms with low overlap (< 0.2)
    student = {
        "branch": "EE",
        "semester": 5,
        "cgpa": 7.5,
        "goal": "Bioinformatics",
    }
    res = recommend(student)
    assert res["weak_match"] is True

    ans, _, _ = explain(res, student)
    assert ("No slot courses strongly match" in ans) or ("No direct matches were found" in ans)


def test_future_options_present():
    """Item 5: Future options lists up to 3 relevant slot courses from later semesters."""
    student = {
        "branch": "EE",
        "semester": 5,
        "cgpa": 7.8,
        "goal": "Software engineering role",
    }
    res = recommend(student)
    assert "future_options" in res
    assert len(res["future_options"]) <= 3

    for fo in res["future_options"]:
        assert fo["semester"] > 5
        assert "missing_prerequisites" in fo
        assert "score" in fo

    ans, _, _ = explain(res, student)
    assert "Upcoming Electives in Later Semesters:" in ans


def test_multi_slot_credits_in_budget():
    """Item 6: Open slots and credit budget calculations."""
    curriculum_ee = get_curriculum_table("EE")
    slots_sem7 = open_slot_info(curriculum_ee, 7)
    assert slots_sem7["open_slots"] == 2
    assert slots_sem7["min_credits_needed"] == 6.0
    assert slots_sem7["max_credits_needed"] == 7.0

    student = {
        "branch": "EE",
        "semester": 7,
        "cgpa": 8.0,
        "goal": "Software engineering role",
    }
    res = recommend(student)
    budget = res["credit_budget"]
    assert budget["open_slots"] == 2
    assert budget["min_credits_needed"] == 6.0
    assert budget["slot_credit_status"] in ["sufficient", "tight", "insufficient"]


def test_template_formatting_no_duplicates_or_broken_grammar():
    """Item 7: Template fixes duplicate course codes, double NPTEL, and broken grammar."""
    student = {
        "branch": "EE",
        "semester": 5,
        "cgpa": 7.8,
        "goal": "Software engineering role",
    }
    res = recommend(student)
    ans, _, _ = explain(res, student)

    # Check for duplicate code format: "**EE3L005** (EE3L005"
    assert "**EE3L005** (EE3L005" not in ans
    # Check for duplicate provider: "(NPTEL) (NPTEL)"
    assert "(NPTEL) (NPTEL)" not in ans
    # Check that broken sentence "This course eligible elective" is gone
    assert "This course eligible elective" not in ans


def test_mocked_llm_explain_path_success_and_payload_shape():
    """Item 8: End-to-end explain path with mocked litellm completion and payload validation."""
    student = {
        "branch": "EE",
        "semester": 7,
        "cgpa": 8.0,
        "goal": "Software engineering role",
    }
    res = recommend(student)

    mock_llm_reply = (
        "Based on your 7.0 credit headroom, I recommend CS6L001 (Computational Intelligence) "
        "and CS4L003 (Artificial Intelligence) which fit your goal in software engineering."
    )

    with patch.dict("os.environ", {"LLM_MODEL": "openai/gpt-4o-mini", "LLM_API_KEY": "sk-mock-valid"}, clear=False):
        with patch("app.llm.client.llm_client.completion", return_value=mock_llm_reply) as mock_comp:
            ans, llm_used, llm_err = explain(res, student)

            assert llm_used is True
            assert llm_err is None
            assert ans == mock_llm_reply

            # Verify payload shape sent to LLM
            mock_comp.assert_called_once()
            call_kwargs = mock_comp.call_args[1]
            messages = call_kwargs["messages"]
            user_msg = messages[1]["content"]

            json_text = user_msg.split("Here is the verified course recommendation data:\n")[1]
            payload = json.loads(json_text)

            assert "student" in payload
            assert "intent" in payload
            assert "credit_budget" in payload
            assert "core_courses" not in payload["credit_budget"]  # Slim payload rule
            assert "recommendations" in payload
            assert "future_options" in payload
            assert "weak_match" in payload


def test_api_recommend_endpoint_success_and_visibility():
    """Item 2: API returns answer, llm_used, llm_error, and data."""
    req = RecommendRequest(
        branch="EE",
        semester=7,
        cgpa=8.5,
        goal="Software engineering role",
        query="what course should I take this semester",
        completed=["EE1L001"],
        avoid=[],
        backlogs=[],
        overload_approved=False,
    )
    with patch("app.llm.client.llm_client.completion", return_value=None):
        response = get_recommendations(req)
        assert response.answer
        assert response.llm_used is False
        assert response.llm_error == "LLM_MODEL not configured"
        assert "credit_budget" in response.data
        assert "recommendations" in response.data
        assert response.data["intent"]["source"] == "profile_goal"
        assert response.data["intent"]["query_had_topic"] is False


def test_api_recommend_endpoint_validation_errors():
    """Verify invalid branch or out-of-range semester raises HTTP 400 or ValidationError."""
    with pytest.raises(HTTPException) as exc_info:
        req = RecommendRequest(branch="CIVIL", semester=4, cgpa=8.0)
        get_recommendations(req)
    assert exc_info.value.status_code == 400
    assert "Invalid branch 'CIVIL'" in exc_info.value.detail

    with pytest.raises((ValidationError, HTTPException)):
        RecommendRequest(branch="EE", semester=0, cgpa=8.0)

    with pytest.raises((ValidationError, HTTPException)):
        RecommendRequest(branch="EE", semester=9, cgpa=8.0)


def test_other_eligible_partition_and_neutral_heading():
    """Verify only score >= MIN_RELEVANCE go into recommendations, rest into other_eligible with neutral heading."""
    # 1. EE Sem 5: no courses match software engineering role
    student_5 = {
        "branch": "EE",
        "semester": 5,
        "cgpa": 7.8,
        "goal": "Software engineering role",
    }
    res_5 = recommend(student_5, query="what course should I take this semester")
    assert len(res_5["recommendations"]) == 0
    assert len(res_5["other_eligible"]) > 0
    for r in res_5["other_eligible"]:
        assert r["score"] < MIN_RELEVANCE

    ans_5, _, _ = explain(res_5, student_5)
    # Checks requirement: When intent.source is profile_goal, say "your goal (<goal text>)"
    assert "your goal (Software engineering role)" in ans_5
    assert "Other eligible electives, not matched to your goal:" in ans_5
    # Checks requirement: Drop the filler phrase and never describe zero-score as recommended
    assert "eligible elective matching semester slot criteria" not in ans_5
    assert "Here are your recommended courses:" not in ans_5

    # 2. EE Sem 7: CS4L003 & CS6L001 match; EC courses do not
    student_7 = {
        "branch": "EE",
        "semester": 7,
        "cgpa": 8.0,
        "goal": "Software engineering role",
    }
    res_7 = recommend(student_7, query="what course should I take this semester")
    rec_cids = [r["course_id"] for r in res_7["recommendations"]]
    other_cids = [r["course_id"] for r in res_7["other_eligible"]]

    assert "CS4L003" in rec_cids
    assert "CS6L001" in rec_cids
    assert "EC4L001" in other_cids
    assert "EC4L002" in other_cids

    for r in res_7["recommendations"]:
        assert r["score"] >= MIN_RELEVANCE
    for r in res_7["other_eligible"]:
        assert r["score"] < MIN_RELEVANCE

    ans_7, _, _ = explain(res_7, student_7)
    assert "Here are your recommended courses:" in ans_7
    assert "Other eligible electives, not matched to your goal:" in ans_7
    assert "eligible elective matching semester slot criteria" not in ans_7


def test_resource_punctuation_formatting_clean():
    """Verify primary resource string formatting cleans stray punctuation like '):.'."""
    student_mme = {
        "branch": "MME",
        "semester": 6,
        "cgpa": 7.5,
        "goal": "Materials research",
    }
    res = recommend(student_mme, query="what course should I take this semester")
    ans, _, _ = explain(res, student_mme)

    assert "):." not in ans
    assert ":." not in ans
    # Check that MME channel resource ends cleanly
    assert "channel (browse by course name)." in ans


def test_unstemmed_original_words_in_matched_terms():
    """Verify user-facing matched_terms display original words rather than stems."""
    scored = score_courses(["CS4L003"], ["artifici", "intelligence"])
    matched = scored["CS4L003"]["matched_terms"]
    assert "artifici" not in matched
    assert "artificial" in matched

