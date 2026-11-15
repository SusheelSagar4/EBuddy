import unittest
from app.contracts.student import StudentProfile
from app.contracts.goal import Goal, GoalRequirement
from app.personas.registry import persona_registry
from app.engine.planner import Planner
from app.engine.validator import PlanValidator
from app.engine.gaps import GapAnalyzer

EE_FOUNDATION = ["MA1L001", "MA1L002", "EE1L001", "CS1L001"]


class TestPlannerPrerequisiteChain(unittest.TestCase):
    """Mandatory core/backlog courses must never be scheduled ahead of an uncleared prerequisite."""

    @classmethod
    def setUpClass(cls):
        persona_registry.discover()
        cls.planner = Planner()
        cls.validator = PlanValidator()
        cls.gap_analyzer = GapAnalyzer()

    def _plan(self, persona_id, sem, backlogs, completed):
        pkg = persona_registry.get(persona_id)
        student = StudentProfile(
            student_id=f"STU_PREREQ_{persona_id}_{sem}_{backlogs}",
            name="Prereq Chain Student",
            programme_id="BTECH_EE",
            current_semester=sem,
            cgpa=8.5,
            backlogs=backlogs,
            is_synthetic=True,
        )
        goal = Goal(goal_id=pkg.spec.goal_id, name="Goal", category="career", description="Goal", source_id="TEST")
        reqs = [
            GoalRequirement(goal_id=goal.goal_id, skill_id=r["skill_id"], required_level=float(r["required_level"]), source_id="TEST")
            for r in pkg.requirements
        ]
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
        plan = self.planner.generate_plan(student, goal, gaps, [], [], completed_course_ids=completed)
        report = self.validator.validate_plan(plan, student, completed_course_ids=completed)
        prereq_check = next(c for c in report.checks if c.check_name == "prerequisites")
        return plan, prereq_check

    def _prior_cores(self, sem):
        cids = list(EE_FOUNDATION)
        for s in range(1, sem):
            for r in self.planner.prog_requirements.get(("BTECH_EE", s), []):
                cid = r.get("course_id", "").strip()
                if cid and cid not in cids:
                    cids.append(cid)
        return cids

    def test_missing_foundation_prereq_is_scheduled_before_core(self):
        """Backlog student missing EE1L001 gets it scheduled ahead of the Sem 5 core EE3L007."""
        completed = [c for c in self._prior_cores(5) if c != "EE1L001"]
        plan, prereq_check = self._plan("btech_upsc", sem=5, backlogs=1, completed=completed)

        self.assertTrue(prereq_check.passed, prereq_check.message)
        course_ids = [it.course_id for it in plan.items if it.item_type == "course"]
        self.assertIn("EE1L001", course_ids)
        self.assertIn("EE3L007", course_ids)
        self.assertLess(course_ids.index("EE1L001"), course_ids.index("EE3L007"))
        prereq_item = next(it for it in plan.items if it.item_type == "course" and it.course_id == "EE1L001")
        self.assertIn("EE3L007", prereq_item.reason.prerequisite_for)

    def test_every_backlog_gap_yields_valid_prereq_order(self):
        """Dropping any single prior course for a backlog student never yields a prerequisite violation."""
        for sem in range(2, 9):
            prior = self._prior_cores(sem)
            for dropped in prior:
                with self.subTest(sem=sem, dropped=dropped):
                    completed = [c for c in prior if c != dropped]
                    _, prereq_check = self._plan("btech_upsc", sem=sem, backlogs=1, completed=completed)
                    self.assertTrue(prereq_check.passed, prereq_check.message)

    def test_sem6_no_backlog_plan_satisfies_prereqs(self):
        """Regression: Sem 6 EE startup student with only Sem 1-4 courses listed must still validate."""
        completed = EE_FOUNDATION + ["EC2L001", "EC2L002", "EE2L001"]
        _, prereq_check = self._plan("student_startup", sem=6, backlogs=0, completed=completed)
        self.assertTrue(prereq_check.passed, prereq_check.message)


if __name__ == "__main__":
    unittest.main()
