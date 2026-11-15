import unittest
from datetime import datetime, timezone
from app.contracts.student import StudentProfile, Constraint
from app.contracts.goal import Goal, GoalRequirement
from app.contracts.proposal import ChangeProposal
from app.personas.registry import persona_registry
from app.engine.planner import Planner
from app.engine.validator import PlanValidator
from app.engine.gaps import GapAnalyzer
from app.agents.agent_1_planner import RoadmapPlannerAgent


class TestRoadmapV2(unittest.TestCase):
    """
    Unit tests for Roadmap v2 functionality:
    - Required vs Choosable separation
    - Determinism across runs with FakeLLM
    - Timeline horizon, semester blocks, exam week workload reduction
    - Adaptive checkpoints (weak score remediation, strong score acceleration)
    - Workload cap shedding (required preserved, extras reduced first)
    - Agent 1 move and replace ChangeProposal handling
    """

    @classmethod
    def setUpClass(cls):
        persona_registry.discover()
        cls.planner = Planner()
        cls.validator = PlanValidator()
        cls.gap_analyzer = GapAnalyzer()
        cls.agent1 = RoadmapPlannerAgent()

    def _create_student(self, student_id="STU_TEST_EE_01", prog="BTECH_EE", sem=5, max_hours=None):
        constraints = []
        if max_hours is not None:
            constraints.append(Constraint(
                constraint_id=f"C_HOURS_{student_id}",
                student_id=student_id,
                constraint_type="weekly_hours",
                parameters={"max_hours": float(max_hours)}
            ))
        return StudentProfile(
            student_id=student_id,
            name="Test Roadmap Student",
            programme_id=prog,
            current_semester=sem,
            cgpa=8.4,
            backlogs=0,
            is_synthetic=True,
        ), constraints

    def test_required_vs_recommended_strictly_disjoint(self):
        """1. REQUIRED courses must never appear in recommended_items."""
        student, constraints = self._create_student("STU_EE_DISJOINT", "BTECH_EE", 5)
        goal = Goal(goal_id="GOAL_EE_CORE_POWER", name="Power Systems", category="career", description="Power", source_id="TEST")
        reqs = [GoalRequirement(goal_id=goal.goal_id, skill_id="SKILL_POWER_FLOW", required_level=4.0, source_id="TEST")]
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
        plan = self.planner.generate_plan(student, goal, gaps, constraints, [], completed_course_ids=["MA1L001", "EE1L001"])

        req_ids = {it.course_id for it in plan.required_courses if it.course_id}
        rec_ids = {it.course_id for it in plan.recommended_items if it.course_id}

        self.assertTrue(len(req_ids) > 0, "Plan should have required core courses")
        self.assertEqual(len(req_ids.intersection(rec_ids)), 0, "Required courses appeared in recommendations")
        for it in plan.required_courses:
            self.assertEqual(it.item_type, "REQUIRED_COURSE")
            self.assertEqual(it.status_badge, "LOCKED")
        for it in plan.recommended_items:
            self.assertNotEqual(it.item_type, "REQUIRED_COURSE")
            self.assertNotEqual(it.status_badge, "LOCKED")

    def test_all_remaining_required_courses_locked(self):
        """2. Every remaining mandatory core course is scheduled as a locked commitment."""
        student, constraints = self._create_student("STU_EE_LOCKED", "BTECH_EE", 5)
        goal = Goal(goal_id="GOAL_EE_CORE_POWER", name="Power Systems", category="career", description="Power", source_id="TEST")
        reqs = [GoalRequirement(goal_id=goal.goal_id, skill_id="SKILL_POWER_FLOW", required_level=4.0, source_id="TEST")]
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
        completed = ["MA1L001", "MA1L002", "EE1L001", "CS1L001", "EC2L001", "EC2L002", "EE2L001"]
        plan = self.planner.generate_plan(student, goal, gaps, constraints, [], completed_course_ids=completed)

        # Sem 5 EE core: EE3L007, EE3L004, EE3L010, EE3L011, EE3P004, EE3P005
        core_ids = {it.course_id for it in plan.required_courses if it.course_id}
        self.assertIn("EE3L007", core_ids)
        self.assertIn("EE3L004", core_ids)
        self.assertIn("EE3L010", core_ids)
        self.assertIn("EE3L011", core_ids)

    def test_semester_blocks_and_exam_week_factor(self):
        """3. Semester blocks use calendar dates and reduce extra load in exam weeks."""
        student, constraints = self._create_student("STU_EE_CAL", "BTECH_EE", 5, max_hours=25.0)
        goal = Goal(goal_id="GOAL_EE_CORE_POWER", name="Power Systems", category="career", description="Power", source_id="TEST")
        reqs = [GoalRequirement(goal_id=goal.goal_id, skill_id="SKILL_POWER_FLOW", required_level=4.0, source_id="TEST")]
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
        plan = self.planner.generate_plan(student, goal, gaps, constraints, [])

        self.assertTrue(len(plan.semester_blocks) >= 1)
        sem5 = plan.semester_blocks[0]
        self.assertEqual(sem5.semester_number, 5)
        self.assertEqual(len(sem5.monthly_themes), 4)

        # Midsem is Month 2, Endsem is Month 4
        m2 = sem5.monthly_themes[1]
        m4 = sem5.monthly_themes[3]
        self.assertTrue(m2.weekly_hours_cap <= 25.0)
        # Endsem has factor 0.4 applied to extra study
        self.assertTrue(m4.weekly_hours_cap <= 10.0)

        # Next 4 weeks check (2 items per week x 4 weeks = 8 items)
        self.assertEqual(len(plan.next_4_weeks), 8)
        for w in plan.next_4_weeks:
            self.assertIn(w.week_index, [1, 2, 3, 4])
            self.assertTrue(w.hours_per_week <= 25.0)

    def test_deterministic_scheduling_with_fakellm(self):
        """4. Planner produces bit-for-bit identical output on consecutive runs."""
        student, constraints = self._create_student("STU_DETERMINISTIC", "BTECH_EE", 5)
        goal = Goal(goal_id="GOAL_EE_CORE_POWER", name="Power Systems", category="career", description="Power", source_id="TEST")
        reqs = [GoalRequirement(goal_id=goal.goal_id, skill_id="SKILL_POWER_FLOW", required_level=4.0, source_id="TEST")]
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])

        plan1 = self.planner.generate_plan(student, goal, gaps, constraints, [])
        plan2 = self.planner.generate_plan(student, goal, gaps, constraints, [])

        self.assertEqual(len(plan1.items), len(plan2.items))
        for it1, it2 in zip(plan1.items, plan2.items):
            self.assertEqual(it1.item_type, it2.item_type)
            self.assertEqual(it1.course_id, it2.course_id)
            self.assertEqual(it1.hours_per_week, it2.hours_per_week)
            self.assertEqual(it1.status_badge, it2.status_badge)

    def test_checkpoint_remediation_and_acceleration(self):
        """5. Weak checkpoint score triggers remediation; strong score accelerates."""
        student, constraints = self._create_student("STU_ADAPT", "BTECH_EE", 5)
        goal = Goal(goal_id="GOAL_EE_CORE_POWER", name="Power Systems", category="career", description="Power", source_id="TEST")
        reqs = [GoalRequirement(goal_id=goal.goal_id, skill_id="SKILL_POWER_FLOW", required_level=4.0, source_id="TEST")]
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
        initial_plan = self.planner.generate_plan(student, goal, gaps, constraints, [])

        # Find checkpoint item
        chk = next(it for it in initial_plan.items if it.item_type == "CHECKPOINT")

        # Weak result (< 50)
        adapted_weak = self.planner.adapt_plan_on_checkpoint(initial_plan, chk.item_id, score=40.0, target_skill="Power Flow Analysis")
        self.assertEqual(len(adapted_weak.items), len(initial_plan.items) + 1)
        rem_items = [it for it in adapted_weak.items if it.item_type == "remediation"]
        self.assertEqual(len(rem_items), 1)
        self.assertEqual(rem_items[0].status_badge, "REMEDIATION")
        self.assertEqual(rem_items[0].hours_per_week, 4.0)
        self.assertIn("Inserted 4.0h remedial bridge", adapted_weak.what_changed_and_why)

        # Strong result (>= 85)
        adapted_strong = self.planner.adapt_plan_on_checkpoint(initial_plan, chk.item_id, score=92.0, target_skill="Power Flow Analysis")
        self.assertIn("Accelerated plan", adapted_strong.what_changed_and_why)
        self.assertEqual(adapted_strong.version, initial_plan.version + 1)

    def test_workload_cap_shedding_preserves_required(self):
        """6. When workload exceeds cap, extras are shed first; required courses are never dropped."""
        # Set a low cap of 10.0 hours/week, while EE Sem 5 core courses alone require > 10 hours
        student, constraints = self._create_student("STU_OVERLOAD", "BTECH_EE", 5, max_hours=10.0)
        goal = Goal(goal_id="GOAL_EE_CORE_POWER", name="Power Systems", category="career", description="Power", source_id="TEST")
        reqs = [GoalRequirement(goal_id=goal.goal_id, skill_id="SKILL_POWER_FLOW", required_level=4.0, source_id="TEST")]
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
        plan = self.planner.generate_plan(student, goal, gaps, constraints, [])

        # Required courses are never dropped
        req_courses = [it for it in plan.required_courses if it.course_id]
        self.assertTrue(len(req_courses) >= 3, "Required courses must not be dropped")
        for it in req_courses:
            self.assertEqual(it.status_badge, "LOCKED")
            self.assertTrue(it.hours_per_week > 0.0)

        # Supplementary extras must be reduced to 0.0
        extra_items = [it for it in plan.items if it not in plan.required_courses]
        for it in extra_items:
            self.assertEqual(it.hours_per_week, 0.0, f"Extra item {it.item_id} was not reduced to 0.0h")

        # Workload cap explanation must be set and explain core course lock
        self.assertIsNotNone(plan.workload_cap_explanation)
        self.assertIn("locked commitments and cannot be dropped", plan.workload_cap_explanation)
        self.assertIn("All supplementary extras", plan.workload_cap_explanation)

    def test_agent_1_move_and_replace_change_proposals(self):
        """7. Agent 1 applies ChangeProposals for move and replace by item ID, triggering re-plan."""
        student, constraints = self._create_student("STU_AGENT1_PROPOSAL", "BTECH_EE", 5)
        goal = Goal(goal_id="GOAL_EE_CORE_POWER", name="Power Systems", category="career", description="Power", source_id="TEST")
        reqs = [GoalRequirement(goal_id=goal.goal_id, skill_id="SKILL_POWER_FLOW", required_level=4.0, source_id="TEST")]
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
        plan = self.planner.generate_plan(student, goal, gaps, constraints, [])

        # Pick a non-prerequisite recommended item or exercise
        target_item = next(it for it in plan.items if it.item_type in ["ELECTIVE_PICK", "exercise", "EXERCISE_SET", "resource"])

        # 1. Move proposal
        move_prop = ChangeProposal(
            proposal_id="PROP_MOVE_001",
            student_id=student.student_id,
            proposer_agent="agent_4_query",
            proposal_type="schedule_shift",
            reasoning="Shift to subsequent semester to manage external commitments.",
            proposed_modifications={
                "move_items": [{"item_id": target_item.item_id, "target_semester": 6}]
            },
            impact_summary="Item shifted to Semester 6",
            status="approved",
            created_at=datetime.now(timezone.utc)
        )

        # Apply proposal via Agent 1 Single-Writer rule
        updated_plan, updated_prop = self.agent1.commit_approved_proposal(plan, student, move_prop)
        self.assertEqual(updated_plan.version, plan.version + 1)
        self.assertEqual(updated_prop.status, "committed")
        moved_item = next(it for it in updated_plan.items if it.item_id == target_item.item_id)
        self.assertEqual(moved_item.semester_number, 6)

        # 2. Replace proposal
        replace_prop = ChangeProposal(
            proposal_id="PROP_REPLACE_002",
            student_id=student.student_id,
            proposer_agent="agent_2_resource",
            proposal_type="resource_swap",
            reasoning="Replace with alternative technical elective.",
            proposed_modifications={
                "replace_items": [{"replace_item_id": moved_item.item_id, "course_id": "EE3L005"}]
            },
            impact_summary="Course replaced with EE3L005",
            status="approved",
            created_at=datetime.now(timezone.utc)
        )

        # Apply replace proposal via Agent 1 Single-Writer rule
        final_plan, final_prop = self.agent1.commit_approved_proposal(updated_plan, student, replace_prop)
        self.assertEqual(final_plan.version, updated_plan.version + 1)
        self.assertEqual(final_prop.status, "committed")
        replaced_items = [it for it in final_plan.items if it.course_id == "EE3L005"]
        self.assertTrue(len(replaced_items) >= 1)


if __name__ == "__main__":
    unittest.main()
