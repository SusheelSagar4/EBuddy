import os
import csv
import unittest
from typing import Set
from app.contracts.student import StudentProfile
from app.contracts.goal import Goal, GoalRequirement
from app.personas.registry import persona_registry
from app.engine.planner import Planner
from app.engine.gaps import GapAnalyzer

class TestUPSCPlanAdjustments(unittest.TestCase):
    """
    Unit tests for UPSC plan item adjustments (Constraint 5):
    - Check 4 passes for Sem 3 EE student.
    - Check 4 passes for Sem 6 MM student (including SKILL_UPSC_OPTIONAL).
    - ee_power_core plan output is unchanged.
    - No verified=FALSE resource is ever assigned as a plan item.
    - Deterministic item generation.
    """
    @classmethod
    def setUpClass(cls):
        persona_registry.discover()
        cls.upsc_pkg = persona_registry.get("btech_upsc")
        cls.ee_pkg = persona_registry.get("ee_power_core")
        cls.planner = Planner()
        cls.gap_analyzer = GapAnalyzer()

        # Load resources.csv to audit verification status
        raw_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "higher_studies", "upsc")
        cls.resources_map = {}
        with open(os.path.join(raw_dir, "resources.csv"), "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                cls.resources_map[r["resource_id"]] = r

    def _get_upsc_goal_and_reqs(self):
        goal = Goal(
            goal_id=self.upsc_pkg.spec.goal_id,
            name="UPSC CSE",
            category="career",
            description="Civil Services",
            source_id="TEST"
        )
        reqs = [
            GoalRequirement(
                goal_id=goal.goal_id,
                skill_id=r["skill_id"],
                required_level=float(r["required_level"]),
                source_id="TEST"
            )
            for r in self.upsc_pkg.requirements
        ]
        return goal, reqs

    def test_01_check_4_passes_sem3_ee(self):
        """Constraint 5: Check 4 passes for a Sem 3 EE student."""
        student = StudentProfile(
            student_id="STU_EE_SEM3_CHK4",
            name="Aarav EE",
            programme_id="BTECH_EE",
            current_semester=3,
            cgpa=8.0,
            backlogs=0,
            is_synthetic=True
        )
        goal, reqs = self._get_upsc_goal_and_reqs()
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
        plan = self.planner.generate_plan(student, goal, gaps, [], [])

        covered_skills: Set[str] = set()
        for it in plan.items:
            covered_skills.update(it.reason.target_skills)

        # All 12 UPSC skills must be covered
        for g in gaps:
            if g["gap"] > 0:
                self.assertIn(
                    g["skill_id"],
                    covered_skills,
                    f"Skill {g['skill_id']} with gap {g['gap']} not covered in plan for Sem 3 EE"
                )

    def test_02_check_4_passes_sem6_mm(self):
        """Constraint 5: Check 4 passes for a Sem 6 MM student (including SKILL_UPSC_OPTIONAL)."""
        student = StudentProfile(
            student_id="STU_MM_SEM6_CHK4",
            name="Ananya MM",
            programme_id="BTECH_MM",
            current_semester=6,
            cgpa=7.5,
            backlogs=0,
            is_synthetic=True
        )
        goal, reqs = self._get_upsc_goal_and_reqs()
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
        plan = self.planner.generate_plan(student, goal, gaps, [], [])

        covered_skills: Set[str] = set()
        for it in plan.items:
            covered_skills.update(it.reason.target_skills)

        # All 12 UPSC skills must be covered
        for g in gaps:
            if g["gap"] > 0:
                self.assertIn(
                    g["skill_id"],
                    covered_skills,
                    f"Skill {g['skill_id']} with gap {g['gap']} not covered in plan for Sem 6 MM"
                )

        # Specifically verify SKILL_UPSC_OPTIONAL is covered via non-course items for MM
        opt_items = [it for it in plan.items if "SKILL_UPSC_OPTIONAL" in it.reason.target_skills]
        self.assertTrue(len(opt_items) >= 1)
        opt_types = {it.item_type for it in opt_items}
        # MM student has no EE2L001 course; optional must be covered via resource and/or exercise
        self.assertTrue("resource" in opt_types or "exercise" in opt_types)

    def test_03_ee_power_core_plan_unchanged(self):
        """Constraint 5: ee_power_core plan output is completely unchanged (byte-identical structure)."""
        student = StudentProfile(
            student_id="STU_EE_CORE_CHK",
            name="EE Core Student",
            programme_id="BTECH_EE",
            current_semester=5,
            cgpa=7.8,
            is_synthetic=True
        )
        goal = Goal(
            goal_id=self.ee_pkg.spec.goal_id,
            name="EE Power Core",
            category="career",
            description="Power Core",
            source_id="TEST"
        )
        reqs = [
            GoalRequirement(
                goal_id=goal.goal_id,
                skill_id=r["skill_id"],
                required_level=float(r["required_level"]),
                source_id="TEST"
            )
            for r in self.ee_pkg.requirements
        ]
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
        plan = self.planner.generate_plan(student, goal, gaps, [], [])

        expected_structure = [
            ('REQUIRED_COURSE', 'EE3L004', ['SKILL_POWER_ELECTRONICS']),
            ('EXERCISE_SET', 'EE3L004', ['SKILL_POWER_ELECTRONICS']),
            ('REQUIRED_COURSE', 'EE3L007', ['SKILL_POWER_SYSTEMS']),
            ('EXERCISE_SET', 'EE3L007', ['SKILL_POWER_SYSTEMS']),
            ('REQUIRED_COURSE', 'EE3L010', []),
            ('EXERCISE_SET', 'EE3L010', []),
            ('REQUIRED_COURSE', 'EE3L011', []),
            ('EXERCISE_SET', 'EE3L011', []),
            ('REQUIRED_COURSE', 'EE3P004', ['SKILL_POWER_ELECTRONICS']),
            ('EXERCISE_SET', 'EE3P004', ['SKILL_POWER_ELECTRONICS']),
            ('REQUIRED_COURSE', 'EE3P005', ['SKILL_INSTRUMENTATION']),
            ('EXERCISE_SET', 'EE3P005', ['SKILL_INSTRUMENTATION']),
            ('ELECTIVE_PICK', 'EE3L005', ['SKILL_CONTROL_SYSTEMS']),
            ('EXERCISE_SET', 'EE3L005', ['SKILL_CONTROL_SYSTEMS']),
            ('ELECTIVE_PICK', 'EC6L012', []),
            ('EXERCISE_SET', 'EC6L012', []),
            ('CHECKPOINT', None, ['SKILL_ELECTRIC_MACHINES', 'SKILL_POWER_SYSTEMS', 'SKILL_CIRCUIT_ANALYSIS', 'SKILL_POWER_ELECTRONICS', 'SKILL_RENEWABLE_ENERGY'])
        ]
        actual_structure = [(it.item_type, it.course_id, it.reason.target_skills) for it in plan.items]
        self.assertEqual(actual_structure, expected_structure)

    def test_04_no_unverified_resource_in_plan(self):
        """Constraint 3 & 5: No resource with verified=FALSE is ever a plan item."""
        for prog in ["BTECH_EE", "BTECH_MM"]:
            student = StudentProfile(
                student_id=f"STU_VER_CHK_{prog}",
                name="Verification Student",
                programme_id=prog,
                current_semester=5,
                is_synthetic=True
            )
            goal, reqs = self._get_upsc_goal_and_reqs()
            gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
            plan = self.planner.generate_plan(student, goal, gaps, [], [])

            resource_items = [it for it in plan.items if it.item_type == "resource"]
            self.assertGreater(len(resource_items), 0)

            for it in resource_items:
                rid = it.resource_id
                self.assertIn(rid, self.resources_map, f"Resource {rid} not found in resources.csv")
                ver = self.resources_map[rid].get("verified", "").strip().upper()
                self.assertEqual(
                    ver,
                    "TRUE",
                    f"Resource {rid} has verified={ver}, which must never be a plan item!"
                )

            # Unverified resources RS08 (Geography) and RS24 (Essay) must NEVER be in plan items
            assigned_rids = {it.resource_id for it in resource_items}
            self.assertNotIn("RS08", assigned_rids)
            self.assertNotIn("RS24", assigned_rids)

            # Check that unverified skills have exercises with 'not confirmed yet'
            unverified_skill_exercises = [
                it for it in plan.items
                if it.item_type == "exercise"
                and any(s in ["SKILL_UPSC_GS1_GEOGRAPHY_SOCIETY", "SKILL_UPSC_ESSAY"] for s in it.reason.target_skills)
            ]
            self.assertEqual(len(unverified_skill_exercises), 2)
            for ex in unverified_skill_exercises:
                self.assertIn(
                    "not confirmed yet",
                    ex.reason.why_this.lower(),
                    f"Exercise for unverified skill {ex.reason.target_skills} must state 'not confirmed yet'"
                )

    def test_05_deterministic_plan_items(self):
        """Constraint 4: Pick resources and exercises deterministically so same inputs give same plan."""
        student = StudentProfile(
            student_id="STU_DETERMINISTIC",
            name="Deterministic Student",
            programme_id="BTECH_MM",
            current_semester=4,
            is_synthetic=True
        )
        goal, reqs = self._get_upsc_goal_and_reqs()
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])

        plan1 = self.planner.generate_plan(student, goal, gaps, [], [])
        plan2 = self.planner.generate_plan(student, goal, gaps, [], [])

        items1 = [(it.item_type, it.resource_id, it.exercise_id, it.reason.target_skills) for it in plan1.items]
        items2 = [(it.item_type, it.resource_id, it.exercise_id, it.reason.target_skills) for it in plan2.items]
        self.assertEqual(items1, items2)

    def test_06_policy_exception_fallback_and_logging(self):
        """Fix 1: When policy.adjust_plan_items raises, error is logged and plan falls back to unadjusted items."""
        student = StudentProfile(
            student_id="STU_ERR_CHK",
            name="Error Test Student",
            programme_id="BTECH_EE",
            current_semester=3,
            cgpa=8.0,
            is_synthetic=True
        )
        goal, reqs = self._get_upsc_goal_and_reqs()
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])

        # Mock adjust_plan_items to raise an exception
        original_adjust = self.upsc_pkg.policy.adjust_plan_items
        try:
            def broken_adjust(s, it, gaps=None):
                raise RuntimeError("Simulated policy crash")

            self.upsc_pkg.policy.adjust_plan_items = broken_adjust

            with self.assertLogs("app.engine.planner", level="ERROR") as log:
                plan = self.planner.generate_plan(student, goal, gaps, [], [])

            # Plan is still produced with fallback unadjusted items
            self.assertIsNotNone(plan)
            self.assertEqual(plan.student_id, student.student_id)
            self.assertGreater(len(plan.items), 0)

            # Error was logged with persona_id 'btech_upsc'
            log_output = "\n".join(log.output)
            self.assertIn("btech_upsc", log_output)
            self.assertIn("Simulated policy crash", log_output)
        finally:
            self.upsc_pkg.policy.adjust_plan_items = original_adjust

if __name__ == "__main__":
    unittest.main()

