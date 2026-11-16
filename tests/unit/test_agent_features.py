import pytest
from datetime import datetime, timezone
from app.contracts.goal import Goal, GoalRequirement
from app.contracts.student import StudentProfile, SkillState, EvidenceItem, Constraint
from app.contracts.chat import ContextCard, Intent
from app.engine.gaps import GapAnalyzer
from app.engine.planner import Planner
from app.engine.diagnostic import AdaptiveDiagnostic
from app.agents.agent_1_planner import RoadmapPlannerAgent
from app.agents.agent_4_query import QueryAdaptationAgent
from app.services.roadmap_orchestrator import roadmap_orchestrator

def test_interest_vs_evidence_conflict_flag():
    """
    Item 7(a): Interest-vs-evidence conflict flag in gap analysis,
    surfaced in plan reason and in chat.
    """
    analyzer = GapAnalyzer()
    planner = Planner()
    agent_4 = QueryAdaptationAgent()

    goal = Goal(
        goal_id="GOAL_EE_CORE_POWER",
        name="Power Systems Engineering",
        category="career",
        description="Power systems",
        source_id="DESIGN_TEAM"
    )
    # Goal requires high mastery in Signals and Systems (85.0)
    reqs = [
        GoalRequirement(
            goal_id=goal.goal_id,
            skill_id="SKILL_SIGNALS_SYSTEMS",
            required_level=85.0,
            importance=1.0,
            source_id="DESIGN_TEAM"
        )
    ]
    # Student diagnostic evidence shows weak proficiency (25.0 < 40)
    evidence = [
        EvidenceItem(
            evidence_id="EV_DIAG_LOW",
            student_id="STU_CONFLICT",
            skill_id="SKILL_SIGNALS_SYSTEMS",
            source_type="diagnostic",
            score=25.0,
            recorded_at=datetime.now(timezone.utc)
        )
    ]
    states = [
        SkillState(
            student_id="STU_CONFLICT",
            skill_id="SKILL_SIGNALS_SYSTEMS",
            estimated_level=25.0,
            confidence=0.9,
            last_updated=datetime.now(timezone.utc)
        )
    ]

    # 1. Gap Analysis should flag conflict
    gaps = analyzer.analyze_gaps(goal, reqs, states, evidence=evidence)
    assert len(gaps) == 1
    assert gaps[0]["conflict_flag"] == "HIGH_INTEREST_LOW_FOUNDATION"
    assert "diagnostic/demonstrated evidence is low" in gaps[0]["conflict_description"]

    # 2. Planner should surface conflict in plan reason and plan.conflict_flag
    student = StudentProfile(
        student_id="STU_CONFLICT",
        name="Conflict Student",
        programme_id="BTECH_EE",
        current_semester=3,
        cgpa=8.0
    )
    plan = planner.generate_plan(student, goal, gaps, [], [])
    assert plan.conflict_flag is not None
    assert "HIGH_INTEREST_LOW_FOUNDATION" in plan.conflict_flag
    conflict_reasons = [it for it in plan.items if "CONFLICT: Interest vs Evidence" in it.reason.why_this]
    assert len(conflict_reasons) > 0

    # 3. Chat (Agent 4) should surface notice in conversational guidance
    card = ContextCard(
        student_id=student.student_id,
        programme_id=student.programme_id,
        current_semester=3,
        cgpa=student.cgpa,
        goal_id=goal.goal_id,
        goal_name=goal.name,
        skill_gaps=[{"skill_id": "SKILL_SIGNALS_SYSTEMS", "estimated_level": 25.0, "confidence": 0.9}],
        current_plan_items=[it.model_dump() for it in plan.items],
        verified_facts=[],
        unverified_advisories=[]
    )
    chat_res = agent_4.handle_query(student.student_id, "Explain my semester plan", card)
    assert "[Notice: Foundational Alignment]" in chat_res["response"]
    assert "foundational gaps in your target area" in chat_res["response"]

def test_weekly_hours_budget_pruning_and_deferral():
    """
    Item 7(b): Weekly-hours budget in the planner, pruning tasks to fit and saying what was deferred.
    """
    agent_1 = RoadmapPlannerAgent()
    student = StudentProfile(
        student_id="STU_BUDGET_TEST",
        name="Budget Student",
        programme_id="BTECH_EE",
        current_semester=3,
        cgpa=8.0
    )
    goal = Goal(goal_id="GOAL_EE_CORE_POWER", name="Power Systems", category="career", description="Power", source_id="DESIGN_TEAM")
    plan = agent_1.planner_engine.generate_plan(student, goal, [], [], [])

    # Weekly budget: 3.0 hours (180 minutes)
    weekly = agent_1.generate_weekly_roadmap(plan, semester_number=3, week_number=1, daily_hours=2.0, weekly_hours_budget=3.0)

    assert weekly.weekly_hours_budget == 3.0
    assert weekly.total_estimated_hours <= 3.0
    assert len(weekly.deferred_tasks) > 0
    assert any("Deferred: exceeds weekly budget" in d for d in weekly.deferred_tasks)

def test_adaptive_diagnostic_scale_and_stop():
    """
    Item 7(c): Simple adaptive diagnostic (start medium difficulty 50, raise/lower by 15,
    stop at confidence threshold >= 0.85, 5-8 items).
    """
    diag = AdaptiveDiagnostic(item_bank=[], min_items=5, max_items=8, confidence_threshold=0.85)

    answers = []
    # Item 1: Start at medium difficulty 50.0
    item1 = diag.select_next_item(["SKILL_CIRCUIT_ANALYSIS"], answers)
    assert item1 is not None
    assert item1.difficulty_0_100 == 50.0

    # Answer 1 correct -> Raise difficulty to 65.0
    answers.append({"exercise_id": item1.exercise_id, "is_correct": True, "difficulty": item1.difficulty_0_100})
    assert not diag.is_complete(answers) # < 5 items, cannot be complete

    item2 = diag.select_next_item(["SKILL_CIRCUIT_ANALYSIS"], answers)
    assert item2.difficulty_0_100 == 65.0

    # Answer 2 correct -> Raise difficulty to 80.0
    answers.append({"exercise_id": item2.exercise_id, "is_correct": True, "difficulty": item2.difficulty_0_100})
    item3 = diag.select_next_item(["SKILL_CIRCUIT_ANALYSIS"], answers)
    assert item3.difficulty_0_100 == 80.0

    # Answer 3 incorrect -> Lower difficulty to 65.0
    answers.append({"exercise_id": item3.exercise_id, "is_correct": False, "difficulty": item3.difficulty_0_100})
    item4 = diag.select_next_item(["SKILL_CIRCUIT_ANALYSIS"], answers)
    assert item4.difficulty_0_100 == 65.0

    # Answer 4 correct
    answers.append({"exercise_id": item4.exercise_id, "is_correct": True, "difficulty": item4.difficulty_0_100})
    assert not diag.is_complete(answers) # 4 items < 5 min items

    # Answer 5 correct -> now 5 items, ability and confidence estimated
    item5 = diag.select_next_item(["SKILL_CIRCUIT_ANALYSIS"], answers)
    answers.append({"exercise_id": item5.exercise_id, "is_correct": True, "difficulty": item5.difficulty_0_100})
    
    # Check stopping condition between 5 and 8 items
    ability, conf = diag.estimate_ability_and_confidence(answers)
    assert 10.0 <= ability <= 95.0
    assert 0.0 <= conf <= 1.0

    # Add items until complete (max 8 items)
    while not diag.is_complete(answers) and len(answers) < 8:
        nxt = diag.select_next_item(["SKILL_CIRCUIT_ANALYSIS"], answers)
        answers.append({"exercise_id": nxt.exercise_id, "is_correct": True, "difficulty": nxt.difficulty_0_100})

    assert diag.is_complete(answers)
    assert 5 <= len(answers) <= 8

def test_rolling_conversation_memory_ops_summary():
    """
    Item 7(d): Rolling per-student conversation summaries written to ops.memory_summary
    and loaded into ContextCard on next turn.
    """
    student_id = "STU_MEMORY_TEST_01"
    # Chat needs a real profile (unknown ids are no longer invented)
    from app.services.onboarding_service import onboarding_service
    onboarding_service.onboard_student(student_id=student_id, name="Memory Test", programme_id="BTECH_EE",
                                       current_semester=5, cgpa=8.0, goal_id="GOAL_EE_CORE_POWER")

    # Turn 1
    res1 = roadmap_orchestrator.chat_turn(student_id, "I have exams approaching next week, what should I study?")
    assert "turn_id" in res1
    
    # Verify memory summary was created
    mem1 = roadmap_orchestrator._load_memory_summary(student_id)
    assert mem1 is not None
    assert "exams" in mem1.lower() or "study" in mem1.lower()

    # Turn 2: Verify memory is loaded into ContextCard
    res2 = roadmap_orchestrator.chat_turn(student_id, "What courses are in my plan?")
    mem2 = roadmap_orchestrator._load_memory_summary(student_id)
    assert mem2 is not None
    # Rolling summary contains history from both interactions
    assert len(mem2) >= len(mem1)

def test_exercise_option_shuffling_and_bias_elimination():
    """
    Item 5: Shuffles MCQ option order at serve time while preserving
    answer key accuracy, eliminating letter position bias.
    """
    import random
    from app.contracts.kb import Exercise
    from app.engine.diagnostic import AdaptiveDiagnostic
    from app.llm.tasks.grader import Grader

    orig = Exercise(
        exercise_id="EX_SHUFFLE_TEST",
        skill_id="SKILL_CIRCUIT_ANALYSIS",
        title="Test Circuit Question",
        question_text="What is the equivalent resistance?",
        exercise_type="mcq",
        options=["A: 10 Ohm", "B: 20 Ohm", "C: 30 Ohm", "D: 40 Ohm"],
        correct_answer="B: 20 Ohm",
        difficulty_0_100=50.0,
        status="draft_for_review",
        source_id="AI_DRAFT",
        verified=True
    )

    grader = Grader()

    # 1. Shuffling with different RNG seeds produces different letter positions
    letters_seen = set()
    for seed in [1, 2, 3, 4, 42, 99]:
        rng = random.Random(seed)
        shuffled = AdaptiveDiagnostic.shuffle_exercise_options(orig, rng=rng)
        assert len(shuffled.options) == 4
        # Verify 20 Ohm is still the designated correct answer
        assert "20 Ohm" in shuffled.correct_answer
        correct_letter = shuffled.correct_answer.split(":")[0].strip()
        letters_seen.add(correct_letter)

        # 2. Grader verifies answer is correct regardless of new shuffled position
        result = grader.grade_answer(shuffled, correct_letter)
        assert result["is_correct"] is True
        assert result["score"] == 100.0

        # Wrong option graded as 0.0
        wrong_letter = "A" if correct_letter != "A" else "B"
        wrong_res = grader.grade_answer(shuffled, wrong_letter)
        assert wrong_res["is_correct"] is False
        assert wrong_res["score"] == 0.0

    # Ensure option has rotated across multiple positions (no static 'B' bias)
    assert len(letters_seen) > 1

def test_diagnostic_convergence_consistent_vs_alternating():
    """
    Item 5: Diagnostic convergence stop rule.
    Stop when n >= 5 and the range of the last 3 theta values <= 4, or n >= 8.
    Confidence must derive from that spread.
    Tests:
      (a) mid-ability alternating student
      (b) consistently strong
      (c) consistently weak
      (d) mixed-then-consistent
    Prints the theta trajectory for each.
    """
    from app.engine.diagnostic import AdaptiveDiagnostic

    diag = AdaptiveDiagnostic(item_bank=[], min_items=5, max_items=8, confidence_threshold=0.85)

    def run_trajectory(answers_stream):
        answers = []
        thetas = []
        for is_corr in answers_stream:
            item = diag.select_next_item(["SKILL_CIRCUIT_ANALYSIS"], answers)
            answers.append({
                "exercise_id": item.exercise_id,
                "is_correct": is_corr,
                "difficulty": item.difficulty_0_100
            })
            thetas.append(diag.compute_running_ability(answers))
            if diag.is_complete(answers):
                break
        ability, conf = diag.estimate_ability_and_confidence(answers)
        return answers, thetas, ability, conf

    # (a) Mid-ability alternating student: [True, False, True, False, True, False, True, False]
    ans_a, thetas_a, ab_a, conf_a = run_trajectory([i % 2 == 0 for i in range(10)])
    print(f"\n[Case A - Alternating] Stopped at n={len(ans_a)} | Trajectory: {thetas_a} | Ability={ab_a} | Confidence={conf_a}")
    assert len(ans_a) == 8
    assert diag.is_complete(ans_a)
    assert conf_a < 0.75  # Spread was large throughout

    # (b) Consistently strong student: [True, True, True, True, True]
    ans_b, thetas_b, ab_b, conf_b = run_trajectory([True] * 8)
    print(f"[Case B - Consistently Strong] Stopped at n={len(ans_b)} | Trajectory: {thetas_b} | Ability={ab_b} | Confidence={conf_b}")
    assert len(ans_b) == 5
    assert thetas_b[-1] == 95.0
    assert max(thetas_b[-3:]) - min(thetas_b[-3:]) <= 4.0
    assert conf_b >= 0.90

    # (c) Consistently weak student: [False, False, False, False, False]
    ans_c, thetas_c, ab_c, conf_c = run_trajectory([False] * 8)
    print(f"[Case C - Consistently Weak] Stopped at n={len(ans_c)} | Trajectory: {thetas_c} | Ability={ab_c} | Confidence={conf_c}")
    assert len(ans_c) == 5
    assert thetas_c[-1] == 10.0
    assert max(thetas_c[-3:]) - min(thetas_c[-3:]) <= 4.0
    assert conf_c >= 0.90

    # (d) Mixed-then-consistent student: [False, True, True, True, True, True, True, True]
    ans_d, thetas_d, ab_d, conf_d = run_trajectory([False] + [True] * 7)
    print(f"[Case D - Mixed-then-Consistent] Stopped at n={len(ans_d)} | Trajectory: {thetas_d} | Ability={ab_d} | Confidence={conf_d}")
    assert len(ans_d) == 8
    assert thetas_d[-1] == 95.0
    assert max(thetas_d[-3:]) - min(thetas_d[-3:]) <= 4.0
    assert conf_d >= 0.90


