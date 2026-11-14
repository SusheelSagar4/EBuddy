import os
import unittest
from datetime import datetime, date, timezone
from app.contracts.student import StudentProfile, EvidenceItem
from app.contracts.goal import Goal, GoalRequirement
from app.personas.registry import persona_registry
from app.personas.btech_upsc.policy import CustomPersonaPolicy
from app.engine.planner import Planner
from app.engine.validator import PlanValidator
from app.engine.gaps import GapAnalyzer
from app.engine.skill_state import SkillStateUpdater

class TestUPSCE2EStudentScenarios(unittest.TestCase):
    """
    Task 5 End-to-End Tests:
    Verifies full lifecycle (milestones, rules, 5-item diagnostic, planning, validation)
    for:
      (1) Sem 3 EE student
      (2) Sem 6 MME student
      (3) Sem 8 EE student
    """
    @classmethod
    def setUpClass(cls):
        persona_registry.discover()
        cls.pkg = persona_registry.get("btech_upsc")
        cls.policy: CustomPersonaPolicy = cls.pkg.policy
        cls.planner = Planner()
        cls.validator = PlanValidator()
        cls.gap_analyzer = GapAnalyzer()
        cls.state_updater = SkillStateUpdater()

        cls.goal = Goal(
            goal_id=cls.pkg.spec.goal_id,
            name="UPSC Civil Services Examination",
            category="competitive_exam",
            description="UPSC CSE preparation",
            source_id="TEST"
        )
        cls.reqs = [
            GoalRequirement(
                goal_id=cls.goal.goal_id,
                skill_id=r["skill_id"],
                required_level=float(r["required_level"]),
                importance=float(r.get("importance", 1.0)),
                source_id="TEST"
            )
            for r in cls.pkg.requirements
        ]

    def test_01_sem3_ee_student(self):
        """
        Scenario 1: Sem 3 EE student.
        - Foundation stage (NEP track).
        - NCERT baseline milestone.
        - 5-item diagnostic assessment.
        - Rules: R4 NCERT baseline gate, R2 CGPA guard, R9 age check.
        - Valid plan generated & passed.
        """
        student = StudentProfile(
            student_id="STU_E2E_EE_SEM3",
            name="Aarav Sharma",
            programme_id="BTECH_EE",
            current_semester=3,
            cgpa=8.2,
            backlogs=0,
            is_synthetic=True
        )

        # 1. 5-item Diagnostic Assessment
        target_skills = self.pkg.diagnostic["blueprint"]["target_skills"]
        self.assertEqual(len(target_skills), 3)
        ev_items = [
            EvidenceItem(
                evidence_id=f"EV_SEM3_{i}",
                student_id=student.student_id,
                skill_id=target_skills[i % len(target_skills)],
                source_type="quiz",
                score=65.0 + (i * 4.0),
                recorded_at=datetime.now(timezone.utc)
            )
            for i in range(5)
        ]
        self.assertEqual(len(ev_items), 5)
        skill_states = self.state_updater.update_states(student.student_id, ev_items)
        self.assertGreaterEqual(len(skill_states), 1)

        # 2. Milestones verification
        sem3_milestones = [m for m in self.pkg.milestones if m.get("semester_target") == 3]
        self.assertEqual(len(sem3_milestones), 1)
        self.assertEqual(sem3_milestones[0]["title"], "NCERT baseline")

        # 3. Rule checks
        r4 = self.policy.r4_baseline_gate(semester=3, ncert_completion=0.6)
        self.assertTrue(r4["triggered"])
        self.assertEqual(r4["forced_milestone"], "upsc_ncert_baseline")

        r2 = self.policy.r2_cgpa_guard(student.cgpa, student.current_semester, programme=student.programme_id)
        self.assertFalse(r2["triggered"])

        r9 = self.policy.r9_age_eligibility(birth_date=date(2005, 10, 1), target_exam_year=2028)
        self.assertTrue(r9["eligible_for_target_year"])

        # 4. Curriculum slot analysis (NEP track from admission year 2025-26)
        slots = self.policy.get_curriculum_slots(student.programme_id, student.current_semester, admission_year="2025-26")
        self.assertEqual(slots["track"], "NEP")

        # 5. Planning and Validation
        gaps = self.gap_analyzer.analyze_gaps(self.goal, self.reqs, skill_states)
        plan = self.planner.generate_plan(student, self.goal, gaps, [], [])
        report = self.validator.validate_plan(plan, student)
        self.assertTrue(report.passed, f"Validation failed: {report.messages}")
        self.assertGreater(len(plan.items), 0)

    def test_02_sem6_mme_student(self):
        """
        Scenario 2: Sem 6 MM student.
        - Pre-NEP track (admitted 2024-25).
        - Answer writing foundation milestone.
        - 5-item diagnostic assessment.
        - Rules: R3 optional gate (with SME review warning for MM), R8 late start.
        - Valid plan generated & passed.
        """
        student = StudentProfile(
            student_id="STU_E2E_MME_SEM6",
            name="Ananya Mishra",
            programme_id="BTECH_MM",
            current_semester=6,
            cgpa=7.4,
            backlogs=0,
            is_synthetic=True
        )

        # 1. 5-item Diagnostic Assessment
        target_skills = self.pkg.diagnostic["blueprint"]["target_skills"]
        ev_items = [
            EvidenceItem(
                evidence_id=f"EV_SEM6_{i}",
                student_id=student.student_id,
                skill_id=target_skills[i % len(target_skills)],
                source_type="quiz",
                score=70.0 + (i * 3.0),
                recorded_at=datetime.now(timezone.utc)
            )
            for i in range(5)
        ]
        self.assertEqual(len(ev_items), 5)
        skill_states = self.state_updater.update_states(student.student_id, ev_items)

        # 2. Milestones verification
        sem6_milestones = [m for m in self.pkg.milestones if m.get("semester_target") == 6]
        self.assertEqual(len(sem6_milestones), 2)
        titles = [m["title"] for m in sem6_milestones]
        self.assertIn("Answer writing foundation", titles)
        self.assertIn("Summer intensive (post Sem 6)", titles)

        # 3. Rule checks
        r3 = self.policy.r3_optional_gate(semester=6, optional_chosen="undecided", programme=student.programme_id)
        self.assertTrue(r3["triggered"])
        self.assertIn("SME-pending", r3["warning"])

        r8 = self.policy.r8_late_start(semester=6, static_pass1_completion=0.45)
        self.assertTrue(r8["triggered"])
        self.assertEqual(r8["recommendation"], "attempt_after_graduation")

        # 4. Optional recommendations & curriculum slots (pre-NEP track from admission year 2024-25)
        opt_rec = self.policy.get_optional_recommendations(student.programme_id)
        self.assertIn("SME", opt_rec["warning"])
        slots = self.policy.get_curriculum_slots(student.programme_id, student.current_semester, admission_year="2024-25")
        self.assertEqual(slots["track"], "2016-17")

        # 5. Planning and Validation
        gaps = self.gap_analyzer.analyze_gaps(self.goal, self.reqs, skill_states)
        plan = self.planner.generate_plan(student, self.goal, gaps, [], [])
        report = self.validator.validate_plan(plan, student)
        self.assertTrue(report.passed, f"Validation failed: {report.messages}")
        self.assertGreater(len(plan.items), 0)

    def test_03_sem8_ee_student(self):
        """
        Scenario 3: Sem 8 EE student.
        - Final attempt year preparation.
        - Prelims mock phase milestone.
        - 5-item diagnostic assessment.
        - Rules: R10 exam clash schedule, R7 attempt decision.
        - Valid plan generated & passed.
        """
        student = StudentProfile(
            student_id="STU_E2E_EE_SEM8",
            name="Rohan Verma",
            programme_id="BTECH_EE",
            current_semester=8,
            cgpa=7.9,
            backlogs=0,
            is_synthetic=True
        )

        # 1. 5-item Diagnostic Assessment
        target_skills = self.pkg.diagnostic["blueprint"]["target_skills"]
        ev_items = [
            EvidenceItem(
                evidence_id=f"EV_SEM8_{i}",
                student_id=student.student_id,
                skill_id=target_skills[i % len(target_skills)],
                source_type="quiz",
                score=82.0 + (i * 2.0),
                recorded_at=datetime.now(timezone.utc)
            )
            for i in range(5)
        ]
        self.assertEqual(len(ev_items), 5)
        skill_states = self.state_updater.update_states(student.student_id, ev_items)

        # 2. Milestones verification
        sem8_milestones = [m for m in self.pkg.milestones if m.get("semester_target") == 8]
        self.assertGreaterEqual(len(sem8_milestones), 1)
        titles = [m["title"] for m in sem8_milestones]
        self.assertIn("Prelims mock phase and attempt decision", titles)

        # 3. Rule checks
        r10 = self.policy.r10_sem8_exam_clash(semester=8, target_attempt_year=2027, current_year=2027)
        self.assertTrue(r10["triggered"])
        self.assertEqual(r10["new_topics_cutoff_date"], "2027-04-22")
        self.assertEqual(r10["clash_window_end"], "2027-05-19")
        self.assertEqual(r10["clash_capped_hours"], 10)
        self.assertEqual(r10["prelims_date"], "2027-05-23")

        r7 = self.policy.r7_attempt_decision(semester=8, static_pass1_completion=0.9, gs_mock_scores=[98.0]*8)
        self.assertTrue(r7["triggered"])
        self.assertEqual(r7["cutoff_benchmark"], "not confirmed yet")

        # 4. Optional recommendations (EE strong overlap)
        opt_rec = self.policy.get_optional_recommendations(student.programme_id)
        self.assertEqual(opt_rec["top_choice"], "Electrical Engineering")

        # 5. Planning and Validation
        gaps = self.gap_analyzer.analyze_gaps(self.goal, self.reqs, skill_states)
        plan = self.planner.generate_plan(student, self.goal, gaps, [], [])
        report = self.validator.validate_plan(plan, student)
        self.assertTrue(report.passed, f"Validation failed: {report.messages}")
        self.assertGreater(len(plan.items), 0)

if __name__ == "__main__":
    unittest.main()

