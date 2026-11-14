import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
from app.api.student import (
    onboard, generate_plan, get_plan, next_diagnostic_question,
    submit_diagnostic_answer, get_mastery, chat,
    OnboardRequest, AnswerRequest, ChatRequest
)
from app.api.simulator import simulate_quiz_score, QuizSimulationRequest
from app.services.plan_service import plan_service

def run_skeleton():
    student_id = "STU_WALK_SKELETON_01"
    print("=" * 70)
    print("WALKING SKELETON: END-TO-END VERIFICATION (Persona: ee_power_core)")
    print("=" * 70)

    # 1. Onboard
    print("\n--- 1. ONBOARDING ---")
    onboard_req = OnboardRequest(
        student_id=student_id,
        name="Aarav Sharma",
        programme_id="BTECH_EE",
        current_semester=3,
        cgpa=8.45,
        backlogs=0,
        goal_id="GOAL_EE_CORE_POWER",
        completed_course_ids=["MA1L001", "PH1L001", "EE1L001", "CS1L001"],
        constraints=[{"type": "MAX_CREDITS", "value": 25}],
        preferences=[{"type": "LEARNING_STYLE", "value": "visual_hands_on"}]
    )
    print("REQUEST: POST /api/student/onboard")
    print(json.dumps(onboard_req.model_dump(), indent=2))
    onboard_res = onboard(onboard_req)
    print("RESPONSE:")
    print(json.dumps({
        "status": onboard_res["status"],
        "student": {
            "student_id": onboard_res["student"]["student_id"],
            "name": onboard_res["student"]["name"],
            "programme_id": onboard_res["student"]["programme_id"],
            "current_semester": onboard_res["student"]["current_semester"],
            "is_synthetic": onboard_res["student"]["is_synthetic"]
        }
    }, indent=2))

    # 2. Diagnostic Question
    print("\n--- 2. ADAPTIVE DIAGNOSTIC (NEXT ITEM) ---")
    print(f"REQUEST: GET /api/student/{student_id}/diagnostic/next")
    diag_res = next_diagnostic_question(student_id)
    print("RESPONSE:")
    print(json.dumps({
        "complete": diag_res["complete"],
        "exercise": {
            "exercise_id": diag_res["exercise"]["exercise_id"],
            "skill_id": diag_res["exercise"]["skill_id"],
            "title": diag_res["exercise"]["title"],
            "question_text": diag_res["exercise"]["question_text"]
        } if not diag_res["complete"] else {}
    }, indent=2))

    # 3. Diagnostic Answer
    print("\n--- 3. ADAPTIVE DIAGNOSTIC (ANSWER SUBMISSION) ---")
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
    print(f"REQUEST: POST /api/student/{student_id}/diagnostic/answer")
    print(json.dumps({
        "exercise_id": ans_req.exercise_id,
        "skill_id": ans_req.skill_id,
        "student_answer": ans_req.student_answer
    }, indent=2))
    ans_res = submit_diagnostic_answer(student_id, ans_req)
    print("RESPONSE:")
    print(json.dumps({
        "exercise_id": ans_res.get("exercise_id"),
        "is_correct": ans_res.get("is_correct"),
        "score": ans_res.get("score"),
        "feedback": ans_res.get("feedback")
    }, indent=2))

    # 4. Gap Report + Plan Generation & Validation
    print("\n--- 4. GAP REPORT + PLAN GENERATION & VALIDATION ---")
    print(f"REQUEST: POST /api/student/{student_id}/plan")
    plan_gen = generate_plan(student_id)
    print("RESPONSE:")
    plan = plan_gen["plan"]
    val = plan_gen["validation"]
    print(json.dumps({
        "plan_id": plan["plan_id"],
        "goal_id": plan["goal_id"],
        "version": plan["version"],
        "total_items": len(plan["items"]),
        "sample_planned_course": {
            "course_id": plan["items"][0]["course_id"],
            "item_type": plan["items"][0]["item_type"],
            "semester_number": plan["items"][0]["semester_number"],
            "reason": plan["items"][0]["reason"]
        },
        "validation_report": {
            "passed": val["passed"],
            "checks_count": len(val["checks"]),
            "messages": val["messages"]
        }
    }, indent=2))

    # 5. Practice / Exercise Submission
    print("\n--- 5. LEARN & PRACTISE EXERCISE SUBMISSION ---")
    practise_req = AnswerRequest(
        exercise_id="EX_PRACTISE_EE301",
        skill_id="SKILL_ELECTRIC_MACHINES",
        title="Transformer Equivalent Circuit",
        question_text="Calculate primary equivalent impedance.",
        exercise_type="numeric",
        options=[],
        correct_answer="5.0 + j8.4",
        student_answer="5.0 + j8.4"
    )
    print(f"REQUEST: POST /api/student/{student_id}/diagnostic/answer (Practise Submission)")
    print(json.dumps({
        "exercise_id": practise_req.exercise_id,
        "skill_id": practise_req.skill_id,
        "student_answer": practise_req.student_answer
    }, indent=2))
    practise_res = submit_diagnostic_answer(student_id, practise_req)
    print("RESPONSE:")
    print(json.dumps({
        "exercise_id": practise_res.get("exercise_id"),
        "is_correct": practise_res.get("is_correct"),
        "score": practise_res.get("score"),
        "feedback": practise_res.get("feedback")
    }, indent=2))

    # 6. Simulator: Strong Quiz Shock
    print("\n--- 6A. SIMULATOR SHOCK: STRONG PERFORMANCE (Score: 95.0) ---")
    sim_strong = QuizSimulationRequest(skill_id="SKILL_CIRCUIT_ANALYSIS", score=95.0)
    print(f"REQUEST: POST /api/sim/{student_id}/quiz")
    print(json.dumps(sim_strong.model_dump(), indent=2))
    res_strong = simulate_quiz_score(student_id, sim_strong)
    print("RESPONSE:")
    print(json.dumps({
        "skill_id": res_strong["skill_id"],
        "score": res_strong["score"],
        "diff": {
            "previous_plan_id": res_strong["diff"]["previous_plan_id"],
            "new_plan_id": res_strong["diff"]["new_plan_id"],
            "summary": res_strong["diff"]["summary"]
        },
        "validation_passed": res_strong["new_plan"]["validation"]["passed"]
    }, indent=2))

    # 6B. Simulator: Weak Quiz Shock (Triggering Remediation)
    print("\n--- 6B. SIMULATOR SHOCK: WEAK PERFORMANCE (Score: 25.0) ---")
    sim_weak = QuizSimulationRequest(skill_id="SKILL_POWER_ELECTRONICS", score=25.0)
    print(f"REQUEST: POST /api/sim/{student_id}/quiz")
    print(json.dumps(sim_weak.model_dump(), indent=2))
    res_weak = simulate_quiz_score(student_id, sim_weak)
    print("RESPONSE:")
    print(json.dumps({
        "skill_id": res_weak["skill_id"],
        "score": res_weak["score"],
        "diff": {
            "previous_plan_id": res_weak["diff"]["previous_plan_id"],
            "new_plan_id": res_weak["diff"]["new_plan_id"],
            "summary": res_weak["diff"]["summary"]
        },
        "validation_passed": res_weak["new_plan"]["validation"]["passed"]
    }, indent=2))

    # 7. Mastery Check
    print("\n--- 7. MASTERY EVALUATION ---")
    print(f"REQUEST: GET /api/student/{student_id}/mastery")
    mastery_res = get_mastery(student_id)
    print("RESPONSE:")
    print(json.dumps({
        "student_id": mastery_res["student_id"],
        "goal_id": mastery_res["goal_id"],
        "status": mastery_res["status"],
        "demonstrated_proficiency": mastery_res["demonstrated_proficiency"],
        "criteria": mastery_res.get("criteria", {}),
        "total_evaluated_skills": len(mastery_res.get("skill_evaluations", []))
    }, indent=2))

    # 8. Chat Turn
    print("\n--- 8. CHAT TURN ---")
    chat_req = ChatRequest(message="Why is Electrical Machines scheduled in Semester 3?")
    print(f"REQUEST: POST /api/student/{student_id}/chat")
    print(json.dumps(chat_req.model_dump(), indent=2))
    chat_res = chat(student_id, chat_req)
    print("RESPONSE:")
    print(json.dumps({
        "turn_id": chat_res.get("turn_id"),
        "inferred_intent": chat_res.get("inferred_intent"),
        "response": chat_res.get("response"),
        "disclaimer": chat_res.get("disclaimer")
    }, indent=2))

if __name__ == "__main__":
    run_skeleton()
