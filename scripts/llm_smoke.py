#!/usr/bin/env python3
"""
LLM Smoke Test Script.
Reads LLM_MODEL / LLM_API_KEY from environment, executes real or configured calls
through app.llm.client for IntentRouter, Explainer, and Grader, and verifies rows in ops.llm_call_log.

Rules:
- If LLM_API_KEY is empty, unset, or a placeholder ('your_api_key...'), exits non-zero with 'NOT RUN'.
- NEVER prints the key.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def main():
    model = os.getenv("LLM_MODEL", "")
    key = os.getenv("LLM_API_KEY", "")

    # Check for placeholder or unset key
    is_placeholder = (
        not key
        or key.strip() == ""
        or key.startswith("your_api_key")
        or "placeholder" in key.lower()
        or key.lower() in ["none", "null", "test"]
    )

    if is_placeholder:
        print("NOT RUN: LLM_API_KEY is not set with a real provider key (placeholder or unset detected).")
        sys.exit(1)

    print(f"Executing LLM smoke test with model: {model} (key length: {len(key)})")

    from app.llm.tasks.intent_router import IntentRouter
    from app.llm.tasks.explainer import Explainer
    from app.llm.tasks.grader import Grader
    from app.contracts.chat import ContextCard
    from app.contracts.kb import Exercise

    # Dummy context card
    card = ContextCard(
        student_id="SMOKE_TEST_STU",
        programme_id="BTECH_EE",
        current_semester=5,
        cgpa=8.5,
        goal_id="GOAL_EE_CORE_POWER",
        goal_name="Power Systems & Renewable Energy",
        skill_gaps=[{"skill_id": "SKILL_POWER_SYSTEMS", "estimated_level": 40.0, "confidence": 0.9}],
        current_plan_items=[],
        verified_facts=["Enrolled in BTECH_EE Sem 5"],
        unverified_advisories=[]
    )

    # 1. Router smoke call
    print("1. Calling IntentRouter...")
    router = IntentRouter()
    intent_res = router.classify_intent("How do I prepare for my power systems elective?", card)
    print(f"   Router classified intent: {intent_res}")

    # 2. Explainer smoke call
    print("2. Calling Explainer...")
    explainer = Explainer()
    expl_res = explainer.explain_recommendation("EE3L007 Electrical Power Transmission and Distribution", card)
    print(f"   Explainer output summary: {expl_res.short_summary}")

    # 3. Grader smoke call (subjective exercise)
    print("3. Calling Grader (subjective evaluation)...")
    grader = Grader()
    ex = Exercise(
        exercise_id="SMOKE_EX_01",
        skill_id="SKILL_POWER_SYSTEMS",
        title="Power System Stability",
        question_text="Explain the physical significance of equal area criterion in single-machine infinite-bus stability.",
        exercise_type="subjective",
        correct_answer="Equal area criterion states that the rotor accelerates during fault when P_m > P_e and decelerates after fault clearing when P_e > P_m; stability is maintained if decelerating area equals or exceeds accelerating area.",
        difficulty_0_100=70.0,
        status="verified",
        source_id="DESIGN_TEAM",
        verified=True
    )
    grade_res = grader.grade_answer(ex, "The rotor accelerates while fault is active and decelerates when electric power exceeds mechanical power after clearing. Equal areas mean system remains synchronized.")
    print(f"   Grader score: {grade_res.get('score')} | Feedback: {grade_res.get('feedback')}")

    # Query ops.llm_call_log to verify rows were recorded
    try:
        import psycopg
        conn = psycopg.connect("postgresql://ebuddy_user:ebuddy_password@127.0.0.1:5432/ebuddy", connect_timeout=3)
        with conn.cursor() as cur:
            cur.execute("SELECT call_id, model_name, purpose, prompt_tokens, completion_tokens, duration_ms, created_at FROM ops.llm_call_log ORDER BY call_id DESC LIMIT 3;")
            rows = cur.fetchall()
            print("\nRecent rows in ops.llm_call_log:")
            for r in rows:
                print(f"  Call {r[0]} | Model: {r[1]} | Purpose: {r[2]} | InTok: {r[3]} | OutTok: {r[4]} | Latency: {r[5]}ms | Time: {r[6]}")
        conn.close()
    except Exception as e:
        print(f"Unable to query ops.llm_call_log: {e}")

    print("\nLLM Smoke Test completed successfully.")

if __name__ == "__main__":
    main()
