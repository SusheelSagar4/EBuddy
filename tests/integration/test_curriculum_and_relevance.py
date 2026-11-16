import pytest
from app.contracts.student import StudentProfile, Constraint, Preference
from app.contracts.goal import Goal
from app.engine.planner import Planner
from app.engine.relevance import CourseRelevanceEngine
from app.engine.rules import RuleEngine
from app.kb.repositories import ResourceRepo, CourseRepo
from app.services.roadmap_orchestrator import roadmap_orchestrator
from app.api.student import (
    onboard, generate_plan, get_plan, get_proposals, decide_proposal, chat,
    OnboardRequest, ProposalDecisionRequest, ChatRequest
)

def test_01_major_course_fixed_regardless_of_low_relevance():
    """
    CRITICAL RULE:
    Major/Core courses are determined by branch curriculum and are FIXED.
    Career relevance scores must NOT determine whether a required major course appears in the roadmap.
    Example: MME student with AI/ML goal must receive ML2L002 (Thermodynamics) even if relevance is 1.
    """
    planner = Planner()
    relevance_engine = CourseRelevanceEngine()

    student = StudentProfile(
        student_id="STU_MME_SEM3_TEST",
        name="Rohan Verma",
        programme_id="BTECH_MM",
        current_semester=3,
        cgpa=8.0,
        backlogs=0
    )
    goal = Goal(
        goal_id="GOAL_CS_AI_ML",
        name="Artificial Intelligence & Machine Learning Engineer",
        category="career",
        description="Core AI/ML engineering",
        source_id="TEST_GOAL"
    )

    # Verify that Thermodynamics has low relevance to AI/ML (score 1/3)
    rel_score, rel_rationale = relevance_engine.get_relevance("ML2L002", goal.goal_id)
    assert rel_score == 1

    # Generate plan
    plan = planner.generate_plan(
        student=student,
        goal=goal,
        gaps=[{"skill_id": "SKILL_DEEP_LEARNING", "gap": 60}],
        constraints=[],
        preferences=[]
    )

    course_items = [it for it in plan.items if it.item_type == "course"]
    course_ids = [it.course_id for it in course_items]

    # Thermodynamics MUST be included because it is fixed major core for MME Sem 3
    assert "ML2L002" in course_ids, "Mandatory core course ML2L002 must not be excluded by low career relevance"

    # Verify the structured reason indicates it is a mandatory branch core requirement
    thermo_item = next(it for it in course_items if it.course_id == "ML2L002")
    assert "Branch Core Degree Requirement" in thermo_item.reason.intent
    assert "Mandatory major/core requirement" in thermo_item.reason.why_this

def test_02_elective_selection_ranks_by_relevance_and_gaps():
    """
    Elective slots ARE recommendation candidates.
    The system ranks eligible electives using CourseRelevanceEngine (0-3 scale)
    plus active skill gap boost.
    """
    relevance_engine = CourseRelevanceEngine()
    rule_engine = RuleEngine()

    # Candidate options for lateral slot in MME: ML2L006, ML3L011, ML3L012
    candidates = ["ML2L006", "ML3L011", "ML3L012"]
    goal_id = "GOAL_CS_AI_ML"
    skill_gaps = [{"skill_id": "SKILL_NANOTECH", "gap": 50}]

    ranked = relevance_engine.rank_electives(
        candidate_course_ids=candidates,
        goal_id=goal_id,
        skill_gaps=skill_gaps,
        completed_course_ids=[],
        prereq_map=rule_engine.prereqs
    )

    assert len(ranked) == 3
    # Top rank should be first and descending
    assert ranked[0]["total_rank"] >= ranked[1]["total_rank"] >= ranked[2]["total_rank"]
    assert all("base_relevance" in r for r in ranked)
    assert all("rationale" in r for r in ranked)

def test_03_minor_course_eligibility_and_recommendation():
    """
    Minor courses are selectable subject to academic eligibility:
    Sem >= 5, CGPA >= 8.0, 0 backlogs.
    If eligible and completed CS1L001 (prerequisite), CS4L003 (Artificial Intelligence) is recommended.
    If ineligible (e.g. CGPA < 8.0 or Sem < 5), minor courses are not recommended.
    """
    planner = Planner()
    goal = Goal(
        goal_id="GOAL_CROSS_SDE_DATA",
        name="Software Engineering & Data Science Transition",
        category="career",
        description="Software & Data Science",
        source_id="TEST"
    )

    # Case A: Eligible student (Sem 5, CGPA 8.5, 0 backlogs, completed CS1L001)
    eligible_student = StudentProfile(
        student_id="STU_MINOR_ELIGIBLE",
        name="Pooja Sharma",
        programme_id="BTECH_MM",
        current_semester=5,
        cgpa=8.5,
        backlogs=0
    )
    plan_eligible = planner.generate_plan(
        student=eligible_student,
        goal=goal,
        gaps=[{"skill_id": "SKILL_ML", "gap": 50}],
        constraints=[],
        preferences=[],
        completed_course_ids=["CS1L001", "MA1L001"]
    )
    minor_items = [it for it in plan_eligible.items if "Minor" in it.reason.intent]
    assert len(minor_items) > 0
    assert minor_items[0].course_id in ["CS4L003", "CS6L001"]
    assert "Approved Minor Course Track" in minor_items[0].reason.intent

    # Case B: Ineligible student (CGPA 7.5 < 8.0)
    ineligible_student = StudentProfile(
        student_id="STU_MINOR_INELIGIBLE",
        name="Amit Patel",
        programme_id="BTECH_MM",
        current_semester=5,
        cgpa=7.5,
        backlogs=0
    )
    plan_ineligible = planner.generate_plan(
        student=ineligible_student,
        goal=goal,
        gaps=[{"skill_id": "SKILL_ML", "gap": 50}],
        constraints=[],
        preferences=[],
        completed_course_ids=["CS1L001", "MA1L001"]
    )
    ineligible_minors = [it for it in plan_ineligible.items if "Minor" in it.reason.intent]
    assert len(ineligible_minors) == 0

def test_04_branch_specific_curriculum_isolation():
    """
    Branch curriculum must strictly isolate major requirements:
    An MME student in Sem 3 must receive MME courses and NOT Electrical Engineering major courses.
    """
    planner = Planner()
    mme_student = StudentProfile(
        student_id="STU_MME_ISOLATION",
        name="Vikas Kumar",
        programme_id="BTECH_MM",
        current_semester=3,
        cgpa=8.0,
        backlogs=0
    )
    goal = Goal(goal_id="GOAL_EE_CORE_POWER", name="Power Systems", category="career", description="Power", source_id="TEST")

    plan = planner.generate_plan(
        student=mme_student,
        goal=goal,
        gaps=[{"skill_id": "SKILL_CIRCUITS", "gap": 80}],
        constraints=[],
        preferences=[]
    )
    course_ids = [it.course_id for it in plan.items if it.item_type == "course"]

    # Must contain MME core courses
    assert "ML2L002" in course_ids
    assert "ML2L003" in course_ids

    # Must NOT contain Electrical Engineering exclusive core courses
    assert "EC2L001" not in course_ids
    assert "EE2S001" not in course_ids

def test_05_resource_retrieval_from_resource_course():
    """
    Resources are retrieved relationally:
    course -> resource_course.csv -> resource.csv
    Verified primary courseware links must be present and valid.
    """
    resource_repo = ResourceRepo()
    primary = resource_repo.get_primary_resource_for_course("ML2L002")

    assert primary is not None
    assert primary.resource_id == "RES_MM_ML2L002_PRIMARY"
    assert "Advanced Metallurgical Thermodynamics" in primary.title
    assert primary.provider == "NPTEL"
    assert primary.url.startswith("https://www.youtube.com/playlist")

def test_06_difficult_resource_returns_backup():
    """
    When student flags a resource as difficult, Agent 2 retrieves
    a verified backup resource from the KB.
    """
    agent_2 = roadmap_orchestrator.agent_2
    alt_res = agent_2.find_alternative_resource(
        current_resource_id="RES_MM_ML2L002_PRIMARY",
        reason="too_difficult"
    )

    assert alt_res["found"] is True
    assert alt_res["resource_id"] == "RES_MM_ML2L002_BACKUP1"
    assert "MIT" in alt_res["title"]
    assert alt_res["url"].startswith("http")

def test_07_no_resource_returns_not_found_message():
    """
    ZERO FABRICATION GUARANTEE:
    If no alternative resource exists in KB, Agent 2 returns explicit not found message
    and NEVER fabricates URLs or fictitious materials.
    """
    agent_2 = roadmap_orchestrator.agent_2
    alt_res = agent_2.find_alternative_resource(
        current_resource_id="RES_NON_EXISTENT_ID_9999",
        reason="too_difficult"
    )

    assert alt_res["found"] is False
    assert alt_res["resource_id"] is None
    assert alt_res["url"] is None
    assert alt_res["message"] == "No suitable resource found in the current knowledge base"

def test_08_agent_isolation_single_writer_guarantee():
    """
    SINGLE-WRITER PRINCIPLE:
    Agent 1 is the ONLY agent that can commit/write a roadmap version.
    Proposals generated by Agent 2, 3, or 4 never mutate the stored roadmap directly.
    """
    student_id = "STU_ISOLATION_TEST_01"
    onboard(OnboardRequest(
        student_id=student_id,
        name="Kavita Sen",
        programme_id="BTECH_MM",
        current_semester=3,
        cgpa=8.1,
        backlogs=0,
        goal_id="GOAL_CS_AI_ML",
        completed_course_ids=["MA1L001", "CS1L001"]
    ))
    res_plan = generate_plan(student_id)
    assert res_plan["version"] == 1

    # Agent 2 proposes a resource swap
    alt = {"resource_id": "RES_MM_ML2L002_BACKUP1", "title": "MIT 3.020", "url": "https://example.com"}
    prop = roadmap_orchestrator.agent_2.propose_resource_swap(
        student_id=student_id,
        current_resource_id="RES_MM_ML2L002_PRIMARY",
        replacement_resource=alt,
        target_week=1,
        reason="Too advanced"
    )
    roadmap_orchestrator.proposals[prop.proposal_id] = prop
    roadmap_orchestrator.student_proposals.setdefault(student_id, []).append(prop.proposal_id)

    # Verify roadmap version has NOT changed
    plan_curr = get_plan(student_id)
    assert plan_curr["version"] == 1

def test_09_proposal_approval_and_rejection_flow():
    """
    Proposal decision lifecycle:
    - Rejection leaves roadmap version intact.
    - Approval commits the proposal through Agent 1 and creates Version N+1.
    """
    student_id = "STU_DECISION_LIFECYCLE"
    onboard(OnboardRequest(
        student_id=student_id,
        name="Tarun Joshi",
        programme_id="BTECH_EE",
        current_semester=3,
        cgpa=8.3,
        backlogs=0,
        goal_id="GOAL_EE_CORE_POWER",
        completed_course_ids=["MA1L001", "CS1L001"]
    ))
    generate_plan(student_id)

    # 1. Rejection flow
    chat_res = chat(
        student_id=student_id,
        req=ChatRequest(message="I have a hackathon this week, please adjust my schedule.")
    )
    prop_id = chat_res["proposal"]["proposal_id"]

    rej = decide_proposal(student_id, prop_id, ProposalDecisionRequest(approve=False, feedback="Not needed now"))
    assert rej["status"] == "rejected"
    assert rej["roadmap_modified"] is False
    assert get_plan(student_id)["version"] == 1

    # 2. Approval flow
    chat_res2 = chat(
        student_id=student_id,
        req=ChatRequest(message="Exam week, reduce my workload to 30 mins a day")
    )
    prop_id2 = chat_res2["proposal"]["proposal_id"]

    appr = decide_proposal(student_id, prop_id2, ProposalDecisionRequest(approve=True, feedback="Approved"))
    assert appr["status"] == "committed"
    assert appr["roadmap_modified"] is True
    assert appr["new_version"] == 2
    assert get_plan(student_id)["version"] == 2

def test_10_elective_with_unmet_prereq_never_recommended():
    """
    Academic Prerequisite Gating:
    An elective with an unmet prerequisite is NEVER recommended, regardless of its relevance score.
    CS4L003 requires CS1L001. A student who has NOT completed CS1L001 must not be recommended CS4L003.
    """
    relevance_engine = CourseRelevanceEngine()
    rule_engine = RuleEngine()

    candidates = ["CS4L003"]
    # Student has completed NO courses (prerequisite CS1L001 is missing)
    ranked = relevance_engine.rank_electives(
        candidate_course_ids=candidates,
        goal_id="GOAL_CS_AI_ML",
        skill_gaps=[{"skill_id": "SKILL_ML", "gap": 100}],
        completed_course_ids=[],
        prereq_map=rule_engine.prereqs
    )

    # Must be completely excluded from recommendations
    assert len(ranked) == 0, "Candidate with unmet prerequisite CS1L001 must be strictly excluded"

    # But if prerequisite is satisfied:
    ranked_satisfied = relevance_engine.rank_electives(
        candidate_course_ids=candidates,
        goal_id="GOAL_CS_AI_ML",
        skill_gaps=[{"skill_id": "SKILL_ML", "gap": 100}],
        completed_course_ids=["CS1L001"],
        prereq_map=rule_engine.prereqs
    )
    assert len(ranked_satisfied) == 1
    assert ranked_satisfied[0]["course_id"] == "CS4L003"
    assert ranked_satisfied[0]["prerequisites_satisfied"] is True

def test_11_student_constraints_hard_while_institute_rules_are_warnings():
    """
    Item 1: Student-stated constraints (credit cap, headroom, weekly hours, not-together pairs, avoid-course)
    are HARD and must never be exceeded by default. Only unsourced institute rules (unsourced_baseline)
    are warnings. Overload courses exceeding student limits go to optional_overload_proposals.
    """
    planner = Planner()
    validator = roadmap_orchestrator.agent_1.validator_engine

    student = StudentProfile(
        student_id="STU_OVERLOAD_TEST",
        name="Ankit Mehra",
        programme_id="BTECH_EE",
        current_semester=5,
        cgpa=8.5,
        backlogs=0
    )
    goal = Goal(
        goal_id="GOAL_EE_CORE_POWER",
        name="Power Systems",
        category="career",
        description="Power",
        source_id="TEST"
    )

    # -------------------------------------------------------------------------
    # PART A: Only unsourced baseline rules (constraints=[]) -> labelled WARNINGS, no courses dropped
    # -------------------------------------------------------------------------
    plan_baseline = planner.generate_plan(
        student=student,
        goal=goal,
        gaps=[],
        constraints=[],
        preferences=[],
        completed_course_ids=["MA1L001", "MA1L002", "EE1L001", "CS1L001", "EC2L001", "EC2L002", "EE2L001"]
    )
    course_items_b = [it for it in plan_baseline.items if it.item_type == "course"]
    assert len(course_items_b) >= 7, "Under baseline rules alone, courses are not dropped"
    warning_items = [it for it in course_items_b if any("unsourced_baseline" in w for w in it.reason.rule_compliance)]
    assert len(warning_items) > 0, "Overload item must carry [WARNING: unsourced_baseline] label"
    report_b = validator.validate_plan(plan_baseline, student, completed_course_ids=["MA1L001", "MA1L002", "EE1L001", "CS1L001", "EC2L001", "EC2L002", "EE2L001"])
    assert report_b.passed is True, "Unsourced baseline warning must not hard-fail validation"

    # -------------------------------------------------------------------------
    # PART B: Student-stated credit cap (HARD) -> Default plan strictly stays within limit
    # -------------------------------------------------------------------------
    c_cap = Constraint(
        constraint_id="C_CAP_24",
        student_id=student.student_id,
        constraint_type="credit_cap",
        parameters={"max_credits": 24.0}
    )
    plan_capped = planner.generate_plan(
        student=student,
        goal=goal,
        gaps=[],
        constraints=[c_cap],
        preferences=[],
        completed_course_ids=["MA1L001", "MA1L002", "EE1L001", "CS1L001", "EC2L001", "EC2L002", "EE2L001"]
    )
    # Default plan must not exceed 24.0 credits
    # Open degree slots (course_id None) carry their own reserved credits on the item.
    total_default_credits = sum(
        (it.credits if it.credits is not None else planner.course_info.get(it.course_id, {}).get("credits", 4.0))
        for it in plan_capped.items if it.item_type == "course")
    assert total_default_credits <= 24.0, f"Default plan exceeded student limit: {total_default_credits} > 24.0"

    # The overload course (minor course) must be in optional_overload_proposals
    assert len(plan_capped.optional_overload_proposals) > 0, "Overload course must be placed in optional proposals"
    prop = plan_capped.optional_overload_proposals[0]
    assert prop["status"] == "pending_student_approval"
    assert "Exceeds student-stated credit limit" in prop["reason"]

    # -------------------------------------------------------------------------
    # PART C: Student-stated avoid_course (HARD)
    # -------------------------------------------------------------------------
    c_avoid = Constraint(
        constraint_id="C_AVOID_CS4L003",
        student_id=student.student_id,
        constraint_type="avoid_course",
        parameters={"course_id": "CS4L003"}
    )
    plan_avoid = planner.generate_plan(
        student=student,
        goal=goal,
        gaps=[],
        constraints=[c_avoid],
        preferences=[],
        completed_course_ids=["MA1L001", "MA1L002", "EE1L001", "CS1L001", "EC2L001", "EC2L002", "EE2L001"]
    )
    plan_course_ids = [it.course_id for it in plan_avoid.items if it.item_type == "course"]
    assert "CS4L003" not in plan_course_ids, "Course in avoid_course must never be scheduled in default plan"
    avoid_props = [p for p in plan_avoid.optional_overload_proposals if p.get("course_id") == "CS4L003"]
    assert len(avoid_props) > 0, "Avoided course placed in optional proposals needing student approval"

def test_12_agent_4_overload_emits_unsourced_baseline_warning_proposal():
    """
    Item 2 & 1: Agent 4 handles credit overload request by generating a proposal
    with [WARNING: unsourced_baseline] rather than hard refusal.
    """
    student_id = "STU_AGENT4_OVERLOAD"
    onboard(OnboardRequest(
        student_id=student_id,
        name="Sanjay Rao",
        programme_id="BTECH_EE",
        current_semester=3,
        cgpa=8.5,
        backlogs=0,
        goal_id="GOAL_EE_CORE_POWER",
        completed_course_ids=["MA1L001", "CS1L001"]
    ))
    generate_plan(student_id)

    chat_res = chat(
        student_id=student_id,
        req=ChatRequest(message="I want to take 30 credits this semester, please overload my courses.")
    )

    assert chat_res["proposal"] is not None, "Agent 4 must produce a proposal rather than hard-blocking"
    assert "[WARNING: unsourced_baseline]" in chat_res["response"]
    assert "unsourced_baseline" in chat_res["proposal"]["impact_summary"]

