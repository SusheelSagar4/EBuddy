import pytest
from app.api.student import (
    onboard, generate_plan, get_plan, get_weekly_roadmap, get_roadmap_versions,
    get_learn_today, get_proposals, decide_proposal, chat,
    submit_diagnostic_answer,
    OnboardRequest, AnswerRequest, ChatRequest, ProposalDecisionRequest
)

def test_four_agents_system_and_single_writer_rule():
    student_id = "STU_FOUR_AGENTS_TEST_01"

    # =========================================================================
    # STAGE 1: Onboard Student & Initial Plan Generation (Agent 1)
    # =========================================================================
    onboard_payload = OnboardRequest(
        student_id=student_id,
        name="Ananya Roy",
        programme_id="BTECH_EE",
        current_semester=3,
        cgpa=8.2,
        backlogs=0,
        goal_id="GOAL_EE_CORE_POWER",
        completed_course_ids=["MA1L001", "PH1L001", "EE1L001", "CS1L001"],
        constraints=[{"type": "MAX_CREDITS", "value": 26}],
        preferences=[{"type": "LEARNING_STYLE", "value": "visual"}]
    )
    res_onboard = onboard(onboard_payload)
    assert res_onboard["status"] == "success"

    # Agent 1 creates initial Roadmap v1
    res_plan = generate_plan(student_id)
    assert res_plan["version"] == 1
    assert "weekly_roadmap" in res_plan
    assert len(res_plan["plan"]["items"]) > 0

    # Retrieve Weekly Roadmap (Agent 1)
    weekly = get_weekly_roadmap(student_id, week=1)
    assert weekly["week_number"] == 1
    assert len(weekly["daily_tasks"]) == 7
    assert weekly["total_estimated_hours"] > 0

    # Verify initial version history has Version 1
    ver_hist = get_roadmap_versions(student_id)
    assert len(ver_hist["versions"]) == 1
    assert ver_hist["versions"][0]["version_number"] == 1

    # =========================================================================
    # STAGE 2: Agent 2 (Learning / Resource Agent)
    # =========================================================================
    learn_res = get_learn_today(student_id)
    assert learn_res["week_number"] == 1
    assert learn_res["total_recommended"] > 0
    # Verified KB link presence
    for r in learn_res["resources"]:
        assert r["url"].startswith("http")
        assert len(r["title"]) > 0

    # Propose resource swap through Agent 2 and verify proposal queue
    from app.services.roadmap_orchestrator import roadmap_orchestrator
    alt_res = roadmap_orchestrator.agent_2.find_alternative_resource(
        current_resource_id=learn_res["resources"][0]["resource_id"],
        reason="too_advanced"
    )
    assert alt_res is not None

    prop_res = roadmap_orchestrator.agent_2.propose_resource_swap(
        student_id=student_id,
        current_resource_id=learn_res["resources"][0]["resource_id"],
        replacement_resource=alt_res,
        target_week=1,
        reason="Student requested beginner-friendly alternative"
    )
    roadmap_orchestrator.proposals[prop_res.proposal_id] = prop_res
    roadmap_orchestrator.student_proposals.setdefault(student_id, []).append(prop_res.proposal_id)

    # Prove Agent 2 DID NOT mutate the roadmap
    plan_after_agent_2 = get_plan(student_id)
    assert plan_after_agent_2["version"] == 1

    # =========================================================================
    # STAGE 3: Agent 3 (Assessment / Quiz Agent)
    # =========================================================================
    # Submit incorrect answer to simulate low score (< 75%)
    ans_req = AnswerRequest(
        exercise_id="EX_EE_DIAG_QUIZ_01",
        skill_id="SKILL_CIRCUIT_ANALYSIS",
        title="Mesh Current Analysis",
        question_text="Determine the loop current in Mesh 2.",
        exercise_type="mcq",
        options=["A: 2A", "B: 5A", "C: 10A", "D: 0A"],
        correct_answer="A: 2A",
        student_answer="D: 0A" # Wrong
    )
    eval_res = submit_diagnostic_answer(student_id, ans_req)
    assert eval_res["score"] == 0.0
    assert eval_res["demonstrated_mastery"] is False
    # Agent 3 generated a remediation proposal!
    assert eval_res["proposal"] is not None
    assert eval_res["proposal"]["proposal_type"] == "remediation_insertion"

    # Prove Agent 3 DID NOT mutate the roadmap directly
    plan_after_agent_3 = get_plan(student_id)
    assert plan_after_agent_3["version"] == 1

    # =========================================================================
    # STAGE 4: Agent 4 (Query / Personal Adaptation Agent)
    # =========================================================================
    # User message requesting exam week workload reduction
    chat_req = ChatRequest(message="I have mid-semester exams this week, can you reduce my workload to 30 mins a day?")
    chat_res = chat(student_id, chat_req)
    assert "proposal" in chat_res
    assert chat_res["proposal"] is not None
    assert chat_res["proposal"]["proposal_type"] == "workload_reduction"
    workload_prop_id = chat_res["proposal"]["proposal_id"]

    # Prove Agent 4 DID NOT mutate the roadmap directly
    plan_after_agent_4 = get_plan(student_id)
    assert plan_after_agent_4["version"] == 1

    # =========================================================================
    # STAGE 5: Student Proposal Decision Flow (Approval & Rejection)
    # =========================================================================
    proposals_pending = get_proposals(student_id)
    assert proposals_pending["pending_count"] >= 2

    # A) REJECTION FLOW: Student rejects the remediation proposal
    remed_prop_id = eval_res["proposal"]["proposal_id"]
    rej_res = decide_proposal(
        student_id=student_id,
        proposal_id=remed_prop_id,
        req=ProposalDecisionRequest(approve=False, feedback="I already understand this topic well.")
    )
    assert rej_res["status"] == "rejected"
    assert rej_res["roadmap_modified"] is False

    # Current roadmap remains at Version 1!
    plan_after_rejection = get_plan(student_id)
    assert plan_after_rejection["version"] == 1

    # B) APPROVAL FLOW: Student approves the workload reduction proposal
    appr_res = decide_proposal(
        student_id=student_id,
        proposal_id=workload_prop_id,
        req=ProposalDecisionRequest(approve=True, feedback="Yes, reduce my workload this week.")
    )
    assert appr_res["status"] == "committed"
    assert appr_res["roadmap_modified"] is True
    assert appr_res["new_version"] == 2

    # Now the canonical roadmap has advanced to Version 2!
    plan_v2 = get_plan(student_id)
    assert plan_v2["version"] == 2

    # Version history has 2 committed versions
    ver_hist_updated = get_roadmap_versions(student_id)
    assert len(ver_hist_updated["versions"]) == 2
    assert ver_hist_updated["versions"][1]["version_number"] == 2
    assert ver_hist_updated["versions"][1]["approved_proposal_id"] == workload_prop_id

