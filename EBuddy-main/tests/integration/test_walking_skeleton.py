import pytest
from app.api.student import (
    onboard, generate_plan, get_plan, next_diagnostic_question,
    submit_diagnostic_answer, get_mastery, chat,
    OnboardRequest, AnswerRequest, ChatRequest
)
from app.api.simulator import simulate_quiz_score, QuizSimulationRequest
from app.api.admin import list_personas, get_stats

def test_walking_skeleton_end_to_end():
    student_id = "STU_WALK_SKELETON_01"

    # Step 1: Onboard student
    onboard_payload = OnboardRequest(
        student_id=student_id,
        name="Rohan Sen",
        programme_id="BTECH_EE",
        current_semester=3,
        cgpa=8.5,
        backlogs=0,
        goal_id="GOAL_EE_CORE_POWER",
        completed_course_ids=["MA1L001", "PH1L001", "EE1L001", "CS1L001"],
        constraints=[{"type": "MAX_CREDITS", "value": 25}],
        preferences=[{"type": "LEARNING_STYLE", "value": "visual"}]
    )
    res_onboard = onboard(onboard_payload)
    assert res_onboard["status"] == "success"
    assert res_onboard["student"]["student_id"] == student_id

    # Step 2: Diagnostic question retrieval
    diag_res = next_diagnostic_question(student_id)
    assert "complete" in diag_res

    # Step 3: Diagnostic submission
    if not diag_res["complete"]:
        ex = diag_res["exercise"]
        ans_req = AnswerRequest(
            exercise_id=ex["exercise_id"],
            skill_id=ex["skill_id"],
            title=ex["title"],
            question_text=ex["question_text"],
            exercise_type=ex.get("exercise_type", "mcq"),
            options=ex.get("options", ["A", "B", "C", "D"]),
            correct_answer=ex.get("correct_answer", "A"),
            student_answer="A"
        )
        res_diag_ans = submit_diagnostic_answer(student_id, ans_req)
        assert "score" in res_diag_ans
        assert "feedback" in res_diag_ans

    # Step 4: Plan generation
    plan_gen = generate_plan(student_id)
    assert "plan" in plan_gen
    assert "validation" in plan_gen
    assert plan_gen["validation"]["passed"] is True
    assert len(plan_gen["plan"]["items"]) > 0

    # Step 5: Plan retrieval
    plan_retrieved = get_plan(student_id)
    assert plan_retrieved["student_id"] == student_id
    assert len(plan_retrieved["items"]) > 0

    # Step 6: Mastery evaluation
    mastery = get_mastery(student_id)
    assert "status" in mastery
    assert "demonstrated_proficiency" in mastery

    # Step 7: Adapt Simulator (inject quiz performance shock)
    sim_req = QuizSimulationRequest(
        skill_id="SKILL_CIRCUIT_ANALYSIS",
        score=95.0
    )
    sim_res = simulate_quiz_score(student_id, sim_req)
    assert "diff" in sim_res
    assert "new_plan" in sim_res
    diff = sim_res["diff"]
    assert "previous_plan_id" in diff
    assert "new_plan_id" in diff

    # Step 8: Buddy Chat (intent routing & grounded answer)
    chat_req = ChatRequest(message="Can you explain why my plan includes Power Electronics?")
    chat_res = chat(student_id, chat_req)
    assert "response" in chat_res
    assert "inferred_intent" in chat_res
    assert len(chat_res["response"]) > 0

    # Step 9: Admin endpoints
    personas = list_personas()
    assert personas["count"] >= 1

    stats = get_stats()
    assert stats["total_courses"] > 0
