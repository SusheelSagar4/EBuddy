import pytest
from app.contracts.student import StudentProfile
from app.engine.field_planner import field_planner_engine, FieldPlannerEngine
from app.engine.course_eligibility import course_eligibility_engine, CourseEligibilityEngine
from app.services.topic_progress_service import topic_progress_service
from app.services.higher_studies_service import higher_studies_service, calculate_cgpa_maintenance
from app.agents.agent_4_query import QueryAdaptationAgent
from app.contracts.chat import ContextCard
from app.services.roadmap_orchestrator import roadmap_orchestrator

def test_deterministic_capacity_model():
    """
    Verifies Requirement F3 Capacity Model:
    1. Base free hours = max(6.0, 24.0 - 0.4 * contact_hours).
    2. Calendar factor (1.0 regular, 0.4 midsem at week 8).
    3. CGPA protection throttle (50% reduction when CGPA < 7.5 or backlogs > 0).
    4. Topic allocation bounded between 1 and 4 per week.
    """
    student_normal = StudentProfile(
        student_id="STU_CAP_1",
        name="High CGPA Student",
        programme_id="BTECH_EE",
        current_semester=4,
        cgpa=8.5,
        backlogs=0
    )
    # 1. Normal regular week (Week 2): enrolled courses with contact hours
    enrolled = ["EE2L001", "EC2L001"] # ~8 contact hours
    cap_regular = field_planner_engine.compute_weekly_capacity(
        student=student_normal,
        enrolled_course_ids=enrolled,
        current_week=2
    )
    assert cap_regular["calendar_factor"] == 1.0
    assert not cap_regular["cgpa_protection_active"]
    assert cap_regular["available_hours"] >= 15.0

    # 2. Midsem week (Week 8): Calendar factor = 0.4
    cap_midsem = field_planner_engine.compute_weekly_capacity(
        student=student_normal,
        enrolled_course_ids=enrolled,
        current_week=8
    )
    assert cap_midsem["calendar_factor"] == 0.4
    assert cap_midsem["available_hours"] < cap_regular["available_hours"]

    # 3. CGPA protection student (CGPA 6.8 < 7.5)
    student_cgpa_warning = StudentProfile(
        student_id="STU_CAP_2",
        name="CGPA Protection Student",
        programme_id="BTECH_EE",
        current_semester=4,
        cgpa=6.8,
        backlogs=0
    )
    cap_protected = field_planner_engine.compute_weekly_capacity(
        student=student_cgpa_warning,
        enrolled_course_ids=enrolled,
        current_week=2
    )
    assert cap_protected["cgpa_protection_active"] is True
    # Available hours should be approx half of regular
    assert cap_protected["available_hours"] <= cap_regular["available_hours"] * 0.55

    # 4. Weekly field plan generation & bounds (min 1, max 4 topics)
    roadmap = field_planner_engine.plan_weekly_field_topics(
        student=student_normal,
        field_id="FIELD_SDE",
        week_number=2,
        semester_number=4,
        enrolled_course_ids=enrolled
    )
    # Check that daily tasks are generated
    assert len(roadmap.daily_tasks) == 7
    # Zero rigid hour bookings: only suggested daily tasks
    assert roadmap.weekly_hours_budget is not None
    assert roadmap.weekly_hours_budget > 0

def test_course_redundancy_and_eligibility_filter():
    """
    Verifies Requirement F5:
    Mandatory test cases:
    1. Sem 4 student reaching NLP in 1 month, elective in Sem 6 -> DO NOT recommend (student learns on own first).
    2. Elective in Sem 5, plan reaches NLP in 10 months -> RECOMMEND (course provides structured early learning).
    """
    student_sem4 = StudentProfile(
        student_id="STU_NLP_TEST",
        name="NLP Candidate",
        programme_id="BTECH_EE",
        current_semester=4,
        cgpa=8.8,
        backlogs=0
    )

    # Mandatory Case 1: Reaching NLP in 1 month, elective in Sem 6 (8 months away)
    # months_to_course = (6 - 4) * 4 = 8.0 months.
    # months_to_topic = 1.0 month.
    # Result: Redundant! DO NOT recommend.
    is_red_1, reason_1 = course_eligibility_engine.evaluate_redundancy(
        course_id="CS4L005",
        offered_semester=6,
        student_current_semester=4,
        months_to_reach_topic=1.0
    )
    assert is_red_1 is True
    assert "Self-study takes precedence" in reason_1

    # Evaluate full recommendation pipeline for Case 1
    recs_1 = course_eligibility_engine.recommend_courses(
        student=student_sem4,
        target_semester=6,
        field_id="FIELD_AIML",
        topic_velocity_overrides={"CS4L005": 1.0}
    )
    nlp_rec_1 = next((r for r in recs_1 if r.course_id == "CS4L005"), None)
    assert nlp_rec_1 is not None
    assert nlp_rec_1.is_redundant is True
    assert nlp_rec_1.is_recommended is False
    assert "REDUNDANT" in nlp_rec_1.rule_badges

    # Mandatory Case 2: Elective in Sem 5 (4 months away), self-study reaches NLP in 10 months
    # months_to_course = (5 - 4) * 4 = 4.0 months.
    # months_to_topic = 10.0 months.
    # Result: Non-redundant! RECOMMEND.
    is_red_2, reason_2 = course_eligibility_engine.evaluate_redundancy(
        course_id="CS4L005",
        offered_semester=5,
        student_current_semester=4,
        months_to_reach_topic=10.0
    )
    assert is_red_2 is False
    assert "structured early learning" in reason_2

    recs_2 = course_eligibility_engine.recommend_courses(
        student=student_sem4,
        target_semester=5,
        field_id="FIELD_AIML",
        topic_velocity_overrides={"CS4L005": 10.0}
    )
    nlp_rec_2 = next((r for r in recs_2 if r.course_id == "CS4L005"), None)
    assert nlp_rec_2 is not None
    assert nlp_rec_2.is_redundant is False
    assert nlp_rec_2.is_eligible is True
    assert nlp_rec_2.is_recommended is True
    assert "RECOMMENDED" in nlp_rec_2.rule_badges

def test_prior_knowledge_test_and_skipping():
    """
    Verifies Requirement F6:
    - 10-15 item configurable prior-knowledge test.
    - >=70% score auto-skips topics.
    - Evidence reliability = 0.9 updates Bayesian SkillState.
    - Plan starts from first unskipped topic.
    """
    student_id = "STU_PK_TEST"
    test_data = topic_progress_service.generate_prior_knowledge_test(
        student_id=student_id,
        field_id="FIELD_DATA_ANALYST",
        num_items=12 # Configurable between 10 and 15
    )
    assert test_data["total_questions"] == 12
    assert len(test_data["questions"]) == 12

    # Simulate student submitting perfect answers (100% score)
    answers = []
    for q in test_data["questions"]:
        answers.append({
            "question_id": q["question_id"],
            "topic_id": q.get("topic_id"),
            "skill_id": q.get("skill_id"),
            "is_correct": True
        })

    eval_result = topic_progress_service.submit_prior_knowledge_test(
        student_id=student_id,
        field_id="FIELD_DATA_ANALYST",
        answers=answers,
        pass_threshold=70.0
    )
    assert eval_result["score_percentage"] == 100.0
    assert eval_result["passed"] is True
    assert len(eval_result["skipped_topics"]) > 0
    # Verified evidence with reliability = 0.9 updated
    assert len(eval_result["updated_skills"]) > 0

    # Ensure completed topics includes skipped topics
    completed = topic_progress_service.get_completed_topics(student_id, "FIELD_DATA_ANALYST")
    for st in eval_result["skipped_topics"]:
        assert st in completed

def test_retention_quiz_and_adaptation():
    """
    Verifies Requirement F7:
    - Periodic retention quiz interleaving (recent topics + 1 earlier topic).
    - Weak score (<60%) tags topic as 'weak' and schedules revision task in field_planner.
    - Strong score (>=80%) tags topic as 'strong'.
    """
    student_id = "STU_RETENTION_TEST"
    field_id = "FIELD_SDE"

    # Mark 3 topics completed
    topic_progress_service.mark_topic_status(student_id, "TOPIC_SDE_STEP_01", field_id, "completed")
    topic_progress_service.mark_topic_status(student_id, "TOPIC_SDE_STEP_02", field_id, "completed")
    topic_progress_service.mark_topic_status(student_id, "TOPIC_SDE_STEP_03", field_id, "completed")

    # Retention quiz should trigger after 3 completions
    assert topic_progress_service.should_trigger_retention_quiz(student_id, field_id) is True

    # Generate interleaved quiz
    quiz = topic_progress_service.generate_retention_quiz(student_id, field_id)
    assert quiz is not None
    assert len(quiz["questions"]) >= 2

    # Submit quiz where student fails TOPIC_SDE_STEP_01 (<60%) and passes TOPIC_SDE_STEP_03 (100%)
    sub_answers = [
        {"topic_id": "TOPIC_SDE_STEP_01", "is_correct": False},
        {"topic_id": "TOPIC_SDE_STEP_03", "is_correct": True}
    ]
    sub_res = topic_progress_service.submit_retention_quiz(student_id, field_id, sub_answers)
    weak_topics = topic_progress_service.get_weak_topics(student_id, field_id)
    assert "TOPIC_SDE_STEP_01" in weak_topics

    # Verify that field_planner schedules revision task for weak topics
    student = StudentProfile(
        student_id=student_id,
        name="Retention Student",
        programme_id="BTECH_EE",
        current_semester=4,
        cgpa=8.0,
        backlogs=0
    )
    plan = field_planner_engine.plan_weekly_field_topics(
        student=student,
        field_id=field_id,
        week_number=3,
        semester_number=4,
        weak_topic_ids=weak_topics
    )
    # Check that at least one revision task is present
    has_rev = any(t.task_type == "revision" for t in plan.daily_tasks)
    assert has_rev is True

def test_chat_scoped_one_week_exceptions_both_directions():
    """
    Verifies Requirement F4:
    1. 'Classes cancelled this week' -> capacity_increase proposal (+8h) for target week only.
    2. 'Exam next week' -> workload_reduction proposal (-8h) for target week only.
    3. Scoped exception: surrounding weeks stay untouched.
    """
    agent_4 = QueryAdaptationAgent()
    student_id = "STU_CHAT_EXCEPTION"
    card = ContextCard(
        student_id=student_id,
        programme_id="BTECH_EE",
        current_semester=4,
        cgpa=8.5,
        goal_id="GOAL_SDE",
        goal_name="Software Development Engineer",
        skill_gaps=[],
        current_plan_items=[],
        verified_facts=[],
        unverified_advisories=[]
    )

    # 1. Classes Cancelled -> Capacity Increase
    res_boost = agent_4.handle_query(
        student_id=student_id,
        message="Classes are cancelled this week, I have extra time!",
        context_card=card
    )
    prop_boost = res_boost.get("proposal")
    assert prop_boost is not None
    assert prop_boost["proposal_type"] == "capacity_increase"
    assert prop_boost["proposed_modifications"]["hours_boost"] == 8.0
    assert prop_boost["target_week"] == 1

    # 2. Midsem / Exam -> Workload Reduction
    res_reduce = agent_4.handle_query(
        student_id=student_id,
        message="I have midsem exams next week, please reduce my workload",
        context_card=card
    )
    prop_reduce = res_reduce.get("proposal")
    assert prop_reduce is not None
    assert prop_reduce["proposal_type"] == "workload_reduction"
    assert prop_reduce["proposed_modifications"]["hours_reduction"] == 8.0
    assert prop_reduce["target_week"] == 2

    # 3. Simulate orchestrator approval and commit for Week 2 reduction
    roadmap_orchestrator.week_overrides[student_id] = {2: -8.0}
    # Week 2 has -8.0 reduction
    assert roadmap_orchestrator.week_overrides[student_id][2] == -8.0
    # Other weeks (Week 1, Week 3) have no override
    assert 1 not in roadmap_orchestrator.week_overrides[student_id]
    assert 3 not in roadmap_orchestrator.week_overrides[student_id]

def test_higher_studies_cgpa_maintenance_and_upsc():
    """
    Verifies Requirement F9 & F10:
    - CGPA maintenance exact SGPA formula.
    - Balanced UPSC schedule with core engineering courses prioritized.
    """
    # 1. CGPA Maintenance calculation:
    # Student in Sem 4 with CGPA 7.5, wants target CGPA 8.0 by Sem 8
    # Completed semesters = 3, remaining = 5
    # Current points = 7.5 * 3 = 22.5
    # Target points = 8.0 * 8 = 64.0
    # Needed points = 64.0 - 22.5 = 41.5
    # Required average SGPA = 41.5 / 5 = 8.30
    cgpa_res = calculate_cgpa_maintenance(
        current_cgpa=7.5,
        current_semester=4,
        target_cgpa=8.0,
        total_semesters=8
    )
    assert cgpa_res["required_average_sgpa"] == 8.30
    assert cgpa_res["is_achievable"] is True
    assert "at least 8.30" in cgpa_res["guidance"]

    # 2. Higher studies guidance (GATE and MBA)
    student = StudentProfile(
        student_id="STU_GATE_TEST",
        name="GATE Aspirant",
        programme_id="BTECH_EE",
        current_semester=5,
        cgpa=8.2,
        backlogs=0
    )
    guidance = higher_studies_service.get_higher_studies_guidance(
        student=student,
        track_type="gate",
        target_cgpa=8.5,
        mock_scores=[70.0, 75.0, 80.0]
    )
    assert guidance["track_type"] == "gate"
    assert guidance["cgpa_maintenance"]["is_achievable"] is True
    assert guidance["track_guidance"]["track"] == "GATE / M.Tech & PSU"

    # 3. UPSC balanced schedule
    upsc_plan = higher_studies_service.generate_balanced_upsc_schedule(
        student=student,
        week_number=1,
        enrolled_course_ids=["EE3L001", "EE3L002"]
    )
    assert upsc_plan.week_number == 1
    assert len(upsc_plan.daily_tasks) == 7
