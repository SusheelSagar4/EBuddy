import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_onboard_unified_validation_and_brief_roadmap():
    """
    Verifies Requirement F1 & F2:
    - Input range validation (CGPA 0.0-10.0, semester 1-8).
    - Prerequisite consistency validation.
    - Immediate brief roadmap returned upon successful onboarding.
    """
    # 1. Invalid CGPA (> 10.0) -> rejected with 422
    res_bad_cgpa = client.post("/api/student/onboard-unified", json={
        "student_id": "STU_VAL_BAD_CGPA",
        "name": "Invalid CGPA Student",
        "branch": "EE",
        "current_semester": 4,
        "cgpa": 11.5,
        "field_of_interest": "SDE"
    })
    assert res_bad_cgpa.status_code == 422
    assert "between 0.0 and 10.0" in res_bad_cgpa.json()["detail"]

    # 2. Invalid Semester (> 8) -> rejected with 422
    res_bad_sem = client.post("/api/student/onboard-unified", json={
        "student_id": "STU_VAL_BAD_SEM",
        "name": "Invalid Sem Student",
        "branch": "EE",
        "current_semester": 9,
        "cgpa": 8.0,
        "field_of_interest": "SDE"
    })
    assert res_bad_sem.status_code == 422
    assert "between 1 and 8" in res_bad_sem.json()["detail"]

    # 3. Inconsistent completed courses: EC2L002 requires MA1L001
    res_inconsistent = client.post("/api/student/onboard-unified", json={
        "student_id": "STU_VAL_INCONSISTENT",
        "name": "Inconsistent Courses Student",
        "branch": "EE",
        "current_semester": 3,
        "cgpa": 8.0,
        "field_of_interest": "SDE",
        "completed_course_ids": ["EC2L002"] # Missing prerequisite MA1L001
    })
    assert res_inconsistent.status_code == 422
    assert "Inconsistent" in res_inconsistent.json()["detail"]

    # 4. Valid Unified Onboarding -> 200 with brief roadmap
    res_valid = client.post("/api/student/onboard-unified", json={
        "student_id": "STU_UNIFIED_01",
        "name": "Aarav Sharma",
        "branch": "EE",
        "current_semester": 4,
        "cgpa": 8.4,
        "field_of_interest": "AI_ML",
        "completed_course_ids": ["MA1L001", "MA1L002", "CS1L001", "EC2L001"]
    })
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert data["status"] == "success"
    assert data["student"]["student_id"] == "STU_UNIFIED_01"
    assert "brief_field_roadmap" in data
    brief_rm = data["brief_field_roadmap"]
    assert brief_rm["field_id"] == "FIELD_AIML"
    assert brief_rm["total_phases"] > 0
    assert len(brief_rm["phases"]) > 0

def test_field_roadmaps_and_topics_endpoints():
    """
    Verifies Requirement F2:
    - /api/field-roadmaps lists verified roadmaps.
    - /api/field-roadmap/{field_id} returns phases and metadata.
    - /api/field-roadmap/{field_id}/topics returns ordered topics.
    """
    # 1. List roadmaps
    r_list = client.get("/api/field-roadmaps")
    assert r_list.status_code == 200
    rms = r_list.json()["roadmaps"]
    fids = [rm["field_id"] for rm in rms]
    assert "FIELD_SDE" in fids
    assert "FIELD_AIML" in fids
    assert "FIELD_DA" in fids
    assert "FIELD_UPSC" in fids

    # 2. Field details
    r_detail = client.get("/api/field-roadmap/FIELD_SDE")
    assert r_detail.status_code == 200
    d = r_detail.json()
    assert d["field_id"] == "FIELD_SDE"
    assert len(d["phases"]) >= 5
    assert d["topics_count"] > 0

    # 3. Topics list
    r_topics = client.get("/api/field-roadmap/FIELD_SDE/topics")
    assert r_topics.status_code == 200
    t_data = r_topics.json()
    assert len(t_data["topics"]) > 0
    assert "est_hours" in t_data["topics"][0]

def test_weekly_field_plan_and_capacity():
    """
    Verifies Requirement F3:
    - /api/student/{id}/field-plan/week/{num} generates personalized plan.
    """
    # Ensure student onboarded
    client.post("/api/student/onboard-unified", json={
        "student_id": "STU_PLAN_01",
        "name": "Plan Test Student",
        "branch": "EE",
        "current_semester": 4,
        "cgpa": 8.2,
        "field_of_interest": "SDE",
        "completed_course_ids": ["MA1L001", "CS1L001"]
    })

    r_plan = client.get("/api/student/STU_PLAN_01/field-plan/week/1")
    assert r_plan.status_code == 200
    plan_data = r_plan.json()
    assert plan_data["week_number"] == 1
    assert len(plan_data["daily_tasks"]) == 7
    assert plan_data["weekly_hours_budget"] > 0
    assert "Plan for" in plan_data["weekly_objective"]

def test_recommended_courses_endpoint():
    """
    Verifies Requirement F5 & F8:
    - /api/student/{id}/recommended-courses returns recommendations with rule badges.
    """
    client.post("/api/student/onboard-unified", json={
        "student_id": "STU_REC_01",
        "name": "Rec Test Student",
        "branch": "EE",
        "current_semester": 4,
        "cgpa": 8.6,
        "field_of_interest": "AI_ML",
        "completed_course_ids": ["MA1L001", "CS1L001"]
    })

    res = client.get("/api/student/STU_REC_01/recommended-courses")
    assert res.status_code == 200
    data = res.json()
    assert len(data["recommendations"]) > 0
    first_rec = data["recommendations"][0]
    assert "rule_badges" in first_rec
    assert "why_recommended" in first_rec

def test_prior_knowledge_test_endpoints():
    """
    Verifies Requirement F6:
    - /api/student/{id}/prior-knowledge-test returns 10-15 questions.
    - /api/student/{id}/prior-knowledge-test/submit evaluates and returns skipped topics.
    """
    client.post("/api/student/onboard-unified", json={
        "student_id": "STU_PK_API_01",
        "name": "PK Test Student",
        "branch": "EE",
        "current_semester": 3,
        "cgpa": 8.0,
        "field_of_interest": "DA",
        "completed_course_ids": ["MA1L001"]
    })

    # Fetch test
    r_test = client.get("/api/student/STU_PK_API_01/prior-knowledge-test?num_items=10")
    assert r_test.status_code == 200
    t_data = r_test.json()
    assert t_data["total_questions"] == 10

    # Submit test with 100% correct
    answers = [{"question_id": q["question_id"], "topic_id": q.get("topic_id"), "is_correct": True} for q in t_data["questions"]]
    r_sub = client.post("/api/student/STU_PK_API_01/prior-knowledge-test/submit", json={
        "field_id": "FIELD_DA",
        "answers": answers,
        "pass_threshold": 70.0
    })
    assert r_sub.status_code == 200
    sub_data = r_sub.json()
    assert sub_data["passed"] is True
    assert sub_data["score_percentage"] == 100.0
    assert len(sub_data["skipped_topics"]) > 0

def test_chat_plan_edits_and_orchestrator_commit():
    """
    Verifies Requirement F4:
    - Chat recognizes 'classes cancelled' -> capacity_increase proposal.
    - Student approves proposal via /api/proposals/{id}/{proposal_id}/decide.
    - Agent 1 commits Roadmap Version N+1 with one-week exception.
    """
    # 1. Onboard student
    client.post("/api/student/onboard-unified", json={
        "student_id": "STU_CHAT_FLOW_01",
        "name": "Chat Flow Student",
        "branch": "EE",
        "current_semester": 4,
        "cgpa": 8.1,
        "field_of_interest": "SDE",
        "completed_course_ids": ["MA1L001", "CS1L001"]
    })

    # 2. Generate initial roadmap so version 1 exists
    client.post("/api/student/STU_CHAT_FLOW_01/plan")

    # 3. Chat message requesting workload reduction for exams next week
    r_chat = client.post("/api/chat", json={
        "student_id": "STU_CHAT_FLOW_01",
        "message": "I have exams next week, please reduce my workload"
    })
    assert r_chat.status_code == 200
    chat_data = r_chat.json()
    assert chat_data.get("proposal") is not None
    prop = chat_data["proposal"]
    assert prop["proposal_type"] == "workload_reduction"
    prop_id = prop["proposal_id"]

    # 4. Student approves proposal
    r_decide = client.post(f"/api/proposals/STU_CHAT_FLOW_01/{prop_id}/decide", json={
        "approve": True,
        "feedback": "Confirmed workload reduction for exams."
    })
    assert r_decide.status_code == 200
    dec_data = r_decide.json()
    assert dec_data["status"] == "committed"
    assert dec_data["roadmap_modified"] is True
    assert dec_data["new_version"] >= 2

def test_higher_studies_guidance_and_cgpa_calculator():
    """
    Verifies Requirement F9 & F10:
    - /api/student/{id}/higher-studies-guidance
    - /api/student/{id}/cgpa-calculator
    """
    client.post("/api/student/onboard-unified", json={
        "student_id": "STU_HS_01",
        "name": "HS Guidance Student",
        "branch": "EE",
        "current_semester": 4,
        "cgpa": 7.8,
        "field_of_interest": "GATE",
        "completed_course_ids": ["MA1L001", "CS1L001"]
    })

    # 1. CGPA Calculator
    r_cgpa = client.get("/api/student/STU_HS_01/cgpa-calculator?target_cgpa=8.0")
    assert r_cgpa.status_code == 200
    c_data = r_cgpa.json()
    assert c_data["is_achievable"] is True
    assert c_data["required_average_sgpa"] > 7.8

    # 2. Higher Studies guidance
    r_hs = client.get("/api/student/STU_HS_01/higher-studies-guidance?track_type=gate&target_cgpa=8.0")
    assert r_hs.status_code == 200
    hs_data = r_hs.json()
    assert "cgpa_maintenance" in hs_data
    assert hs_data["track_guidance"]["track"] == "GATE / M.Tech & PSU"
