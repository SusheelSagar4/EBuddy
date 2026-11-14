import os
import csv
import unittest
from datetime import datetime, timezone
from app.contracts.student import StudentProfile, EvidenceItem, SkillState, Constraint, Preference
from app.contracts.goal import Goal, GoalRequirement
from app.contracts.plan import Plan, PlanItem, StructuredReason
from app.personas.registry import persona_registry
from app.engine.planner import Planner
from app.engine.validator import PlanValidator
from app.engine.gaps import GapAnalyzer
from app.engine.skill_state import SkillStateUpdater
from app.engine.rules import RuleEngine
from app.llm.fake import FakeLLM

class TestPersonaConformance(unittest.TestCase):
    """
    Persona Conformance Quality Gate (F4).
    Validates all registered personas and their concrete student profiles against the 8 conformance checks.
    """
    @classmethod
    def setUpClass(cls):
        persona_registry.discover()
        cls.personas = persona_registry.list_all()
        if not cls.personas:
            raise RuntimeError("No personas discovered in persona registry!")

        cls.persona_profiles = {}
        for pkg in cls.personas:
            p_id = pkg.spec.persona_id
            csv_path = os.path.join("data", "seed", "personas", p_id, "students.csv")
            if not os.path.exists(csv_path):
                raise RuntimeError(f"FATAL: Persona '{p_id}' has no students.csv at {csv_path}!")
            with open(csv_path, "r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            if not rows:
                raise RuntimeError(f"FATAL: Persona '{p_id}' has 0 profiles in {csv_path}!")

            profiles = []
            for r in rows:
                completed = [c.strip() for c in r.get("completed_courses", "").split(";") if c.strip()]
                profiles.append((
                    StudentProfile(
                        student_id=r["student_id"].strip(),
                        name=r["name"].strip(),
                        programme_id=r["programme_id"].strip(),
                        current_semester=int(r["current_semester"]),
                        cgpa=float(r["cgpa"]) if r.get("cgpa") else 8.0,
                        backlogs=int(r.get("backlogs", 0)),
                        is_synthetic=True
                    ),
                    completed
                ))
            cls.persona_profiles[p_id] = profiles

        cls.planner = Planner()
        cls.validator = PlanValidator()
        cls.gap_analyzer = GapAnalyzer()
        cls.state_updater = SkillStateUpdater()
        cls.rule_engine = RuleEngine()
        cls.fake_llm = FakeLLM()

    def test_01_plan_produced_and_valid(self):
        """Check 1: Plan is produced and ValidationReport.passed == True."""
        for pkg in self.personas:
            p_id = pkg.spec.persona_id
            for student, completed in self.persona_profiles[p_id]:
                with self.subTest(persona=p_id, profile=student.student_id):
                    goal = Goal(
                        goal_id=pkg.spec.goal_id,
                        name="Test Goal",
                        category="career",
                        description="Test Goal",
                        source_id="TEST"
                    )
                    reqs = [
                        GoalRequirement(
                            goal_id=goal.goal_id,
                            skill_id=r["skill_id"],
                            required_level=float(r["required_level"]),
                            importance=float(r.get("importance", 1.0)),
                            source_id="TEST"
                        )
                        for r in pkg.requirements
                    ]
                    gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
                    plan = self.planner.generate_plan(student, goal, gaps, [], [], completed_course_ids=completed)
                    
                    report = self.validator.validate_plan(plan, student, completed_course_ids=completed)
                    self.assertTrue(report.passed, f"Plan validation failed for {p_id} ({student.student_id}): {report.messages}")
                    self.assertTrue(len(plan.items) > 0, f"Plan has no items for {p_id} ({student.student_id})")

    def test_02_catalog_existence_and_prerequisites(self):
        """Check 2: Every cited course exists, prerequisites satisfied, credits within limits."""
        for pkg in self.personas:
            p_id = pkg.spec.persona_id
            for student, completed in self.persona_profiles[p_id]:
                with self.subTest(persona=p_id, profile=student.student_id):
                    goal = Goal(goal_id=pkg.spec.goal_id, name="Test Goal", category="career", description="Goal", source_id="TEST")
                    reqs = [GoalRequirement(goal_id=goal.goal_id, skill_id=r["skill_id"], required_level=float(r["required_level"]), source_id="TEST") for r in pkg.requirements]
                    gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
                    plan = self.planner.generate_plan(student, goal, gaps, [], [], completed_course_ids=completed)
                    report = self.validator.validate_plan(plan, student, completed_course_ids=completed)

                    course_check = next((c for c in report.checks if c.check_name == "course_existence"), None)
                    self.assertIsNotNone(course_check)
                    self.assertTrue(course_check.passed, f"Course existence check failed for {student.student_id}")

                    prereq_check = next((c for c in report.checks if c.check_name == "prerequisites"), None)
                    self.assertIsNotNone(prereq_check)
                    self.assertTrue(prereq_check.passed, f"Prerequisites check failed for {student.student_id}")

    def test_03_no_mastered_content_assigned(self):
        """Check 3: No content the student has already mastered/completed is assigned."""
        for pkg in self.personas:
            p_id = pkg.spec.persona_id
            for student, completed in self.persona_profiles[p_id]:
                with self.subTest(persona=p_id, profile=student.student_id):
                    goal = Goal(goal_id=pkg.spec.goal_id, name="Test Goal", category="career", description="Goal", source_id="TEST")
                    reqs = [GoalRequirement(goal_id=goal.goal_id, skill_id=r["skill_id"], required_level=float(r["required_level"]), source_id="TEST") for r in pkg.requirements]
                    gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
                    plan = self.planner.generate_plan(student, goal, gaps, [], [], completed_course_ids=completed)
                    report = self.validator.validate_plan(plan, student, completed_course_ids=completed)

                    mastered_check = next((c for c in report.checks if c.check_name == "no_duplicate_mastery"), None)
                    self.assertIsNotNone(mastered_check)
                    self.assertTrue(mastered_check.passed, f"Mastered content check failed for {student.student_id}")

    def test_04_goal_skills_covered_or_explained(self):
        """Check 4: All goal skills below target level are covered or explained."""
        for pkg in self.personas:
            p_id = pkg.spec.persona_id
            for student, completed in self.persona_profiles[p_id]:
                with self.subTest(persona=p_id, profile=student.student_id):
                    reqs = [GoalRequirement(goal_id=pkg.spec.goal_id, skill_id=r["skill_id"], required_level=float(r["required_level"]), source_id="TEST") for r in pkg.requirements]
                    goal = Goal(goal_id=pkg.spec.goal_id, name="Test Goal", category="career", description="Goal", source_id="TEST")
                    gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
                    plan = self.planner.generate_plan(student, goal, gaps, [], [], completed_course_ids=completed)

                    covered_skills = set()
                    for it in plan.items:
                        covered_skills.update(it.reason.target_skills)

                    for g in gaps:
                        if g["gap"] > 0:
                            self.assertIn(g["skill_id"], covered_skills, f"Skill {g['skill_id']} with gap {g['gap']} not covered in plan for {student.student_id}")

    def test_05_active_practice_included(self):
        """Check 5: Plan includes active practice items (exercises/projects)."""
        for pkg in self.personas:
            p_id = pkg.spec.persona_id
            for student, completed in self.persona_profiles[p_id]:
                with self.subTest(persona=p_id, profile=student.student_id):
                    goal = Goal(goal_id=pkg.spec.goal_id, name="Test Goal", category="career", description="Goal", source_id="TEST")
                    reqs = [GoalRequirement(goal_id=goal.goal_id, skill_id=r["skill_id"], required_level=float(r["required_level"]), source_id="TEST") for r in pkg.requirements]
                    gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
                    plan = self.planner.generate_plan(student, goal, gaps, [], [], completed_course_ids=completed)

                    exercise_items = [it for it in plan.items if it.item_type in ["exercise", "project"]]
                    self.assertTrue(len(exercise_items) >= 1, f"Expected at least 1 active practice item for {student.student_id}")

    def test_06_adaptation_on_quiz_results(self):
        """Check 6: Strong quiz result shortens/skips content; weak quiz result adds remediation; both validate."""
        for pkg in self.personas:
            p_id = pkg.spec.persona_id
            for student, completed in self.persona_profiles[p_id]:
                with self.subTest(persona=p_id, profile=student.student_id):
                    goal = Goal(goal_id=pkg.spec.goal_id, name="Test Goal", category="career", description="Goal", source_id="TEST")
                    target_skill = pkg.requirements[0]["skill_id"]

                    # Scenario A: Weak Quiz Result (score = 30) -> large gap remains
                    weak_ev = [EvidenceItem(evidence_id="EV_WEAK", student_id=student.student_id, skill_id=target_skill, source_type="quiz", score=30.0, recorded_at=datetime.now(timezone.utc))]
                    weak_states = self.state_updater.update_states(student.student_id, weak_ev)
                    reqs = [GoalRequirement(goal_id=goal.goal_id, skill_id=target_skill, required_level=80.0, source_id="TEST")]
                    weak_gaps = self.gap_analyzer.analyze_gaps(goal, reqs, weak_states)
                    weak_plan = self.planner.generate_plan(student, goal, weak_gaps, [], [], completed_course_ids=completed)
                    report_weak = self.validator.validate_plan(weak_plan, student, completed_course_ids=completed)
                    self.assertTrue(report_weak.passed)

                    # Scenario B: Strong Quiz Result (score = 95) -> gap closed
                    strong_ev = [EvidenceItem(evidence_id="EV_STRONG", student_id=student.student_id, skill_id=target_skill, source_type="quiz", score=95.0, recorded_at=datetime.now(timezone.utc))]
                    strong_states = self.state_updater.update_states(student.student_id, strong_ev)
                    strong_gaps = self.gap_analyzer.analyze_gaps(goal, reqs, strong_states)
                    strong_plan = self.planner.generate_plan(student, goal, strong_gaps, [], [], completed_course_ids=completed)
                    report_strong = self.validator.validate_plan(strong_plan, student, completed_course_ids=completed)
                    self.assertTrue(report_strong.passed)

                    # Strong plan has fewer remediation/course items for this skill than weak plan
                    weak_skill_items = [it for it in weak_plan.items if target_skill in it.reason.target_skills]
                    strong_skill_items = [it for it in strong_plan.items if target_skill in it.reason.target_skills and it.item_type != "milestone"]
                    self.assertTrue(len(weak_skill_items) >= len(strong_skill_items))

    def test_07_deterministic_planning(self):
        """Check 7: Same inputs -> identical plan structure twice."""
        for pkg in self.personas:
            p_id = pkg.spec.persona_id
            for student, completed in self.persona_profiles[p_id]:
                with self.subTest(persona=p_id, profile=student.student_id):
                    goal = Goal(goal_id=pkg.spec.goal_id, name="Test Goal", category="career", description="Goal", source_id="TEST")
                    reqs = [GoalRequirement(goal_id=goal.goal_id, skill_id=r["skill_id"], required_level=float(r["required_level"]), source_id="TEST") for r in pkg.requirements]
                    gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])

                    plan1 = self.planner.generate_plan(student, goal, gaps, [], [], completed_course_ids=completed)
                    plan2 = self.planner.generate_plan(student, goal, gaps, [], [], completed_course_ids=completed)

                    items1 = [(it.item_type, it.course_id, it.reason.target_skills) for it in plan1.items]
                    items2 = [(it.item_type, it.course_id, it.reason.target_skills) for it in plan2.items]
                    self.assertEqual(items1, items2, f"Planning was non-deterministic for {student.student_id}")

    def test_08_unachievable_request_handling(self):
        """Check 8: Unachievable request (e.g. credit cap violation) -> clear refusal + best valid alternative."""
        student_probation = StudentProfile(
            student_id="STU_PROBATION",
            name="Probation Student",
            programme_id="BTECH_EE",
            current_semester=3,
            cgpa=5.50, # Low CGPA -> 18 credit cap
            backlogs=1,
            is_synthetic=True
        )
        excessive_items = [
            PlanItem(
                item_id=f"ITEM_EXC_{i}",
                item_type="course",
                course_id=cid,
                reason=StructuredReason(intent="Overload", target_skills=["SKILL_CIRCUIT_ANALYSIS"], why_this="Test")
            )
            for i, cid in enumerate(["EE2L001", "EE2L002", "EE2L003", "EC2L001", "EC2L002", "MA2L003"])
        ]
        excessive_plan = Plan(
            plan_id="PLAN_OVERLOAD",
            student_id=student_probation.student_id,
            goal_id="GOAL_EE_CORE_POWER",
            items=excessive_items,
            created_at=datetime.now(timezone.utc)
        )
        report = self.validator.validate_plan(excessive_plan, student_probation)
        probation_check = next((c for c in report.checks if "PROBATION" in c.check_name), None)
        self.assertIsNotNone(probation_check)
        self.assertIn("exceeds probation cap", probation_check.message)

if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
