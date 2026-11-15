import os
import unittest
from app.personas.registry import persona_registry
from app.personas.student_startup.policy import CustomPersonaPolicy

class TestStartupCurriculumSlotWiring(unittest.TestCase):
    """
    Task 4 Unit Tests:
    Validates curriculum slot wiring using shared institute_curriculum_slots.csv:
    - Track resolution from admission year (NEP vs 2016-17 pre-NEP)
    - Heavy and light slot classification per programme (BTECH_EE and BTECH_MM)
    - Scheduling venture hours around labs and project semesters
    - Sem 8 project alignment (S7) surfaced as a prompt only
    """
    @classmethod
    def setUpClass(cls):
        persona_registry.discover()
        pkg = persona_registry.get("student_startup")
        assert pkg is not None, "student_startup persona missing from registry"
        cls.policy = pkg.policy

    def test_01_track_resolution_from_admission_year(self):
        """Track rule: admitted 2025-26 or later = NEP; earlier = 2016-17 pre-NEP."""
        # Admitted 2025-26 or later -> NEP
        slots_2025 = self.policy.get_curriculum_slots("BTECH_EE", 3, admission_year="2025-26")
        self.assertEqual(slots_2025["track"], "NEP")

        slots_2026 = self.policy.get_curriculum_slots("BTECH_EE", 1, admission_year="2026-27")
        self.assertEqual(slots_2026["track"], "NEP")

        # Admitted prior to 2025-26 -> 2016-17 pre-NEP
        slots_2024 = self.policy.get_curriculum_slots("BTECH_EE", 5, admission_year="2024-25")
        self.assertEqual(slots_2024["track"], "2016-17")

        slots_2023 = self.policy.get_curriculum_slots("BTECH_EE", 7, admission_year="2023-24")
        self.assertEqual(slots_2023["track"], "2016-17")

    def test_02_ee_heavy_and_light_slots_classification(self):
        """Verify heavy (Core/Lab) vs light (Breadth/Seminar) slot classification for EE."""
        res_sem3 = self.policy.get_curriculum_slots("BTECH_EE", 3, track="2016-17")
        self.assertGreater(len(res_sem3["heavy_slots"]), 0)
        self.assertGreater(len(res_sem3["light_slots"]), 0)

        heavy_titles = [s.get("course_title", "").lower() for s in res_sem3["heavy_slots"]]
        light_titles = [s.get("course_title", "").lower() for s in res_sem3["light_slots"]]

        # Labs and core courses in heavy slots
        self.assertTrue(any("laboratory" in t or "signals" in t or "electronics" in t for t in heavy_titles))
        # Breadth and Seminar in light slots
        self.assertTrue(any("breadth" in t or "seminar" in t for t in light_titles))

        # Academic workload and venture hours budget
        self.assertGreater(res_sem3["estimated_academic_hours"], 0)
        self.assertGreaterEqual(res_sem3["recommended_weekly_venture_hours"], 5.0)

    def test_03_mm_curriculum_slot_wiring(self):
        """Verify slot wiring and venture hours scheduling for BTECH_MM."""
        res_mm_sem6 = self.policy.get_curriculum_slots("BTECH_MM", 6, track="2016-17")
        self.assertEqual(res_mm_sem6["programme"], "BTECH_MM")
        self.assertGreater(res_mm_sem6["total_slots"], 0)

        # Workload hours quantified
        self.assertGreater(res_mm_sem6["estimated_academic_hours"], 0)
        self.assertGreaterEqual(res_mm_sem6["recommended_weekly_venture_hours"], 5.0)

    def test_04_heavy_vs_light_semesters_scheduling(self):
        """Verify venture hours are scheduled around lab-heavy and project semesters."""
        # Sem 7 has project / BTP evaluation
        res_sem7 = self.policy.get_curriculum_slots("BTECH_EE", 7, track="2016-17")
        self.assertTrue(res_sem7["is_heavy_semester"])

        # Venture hours are bounded and quantified
        self.assertLessEqual(res_sem7["recommended_weekly_venture_hours"], 15.0)
        self.assertGreaterEqual(res_sem7["recommended_weekly_venture_hours"], 5.0)

    def test_05_sem8_project_alignment_prompt_only(self):
        """Verify Sem 8 project alignment (S7) is surfaced as a prompt only."""
        res_sem8 = self.policy.get_curriculum_slots("BTECH_EE", 8, track="2016-17")
        prompt = res_sem8.get("project_alignment_prompt")
        self.assertIsNotNone(prompt)
        self.assertIn("aligning", prompt.lower())
        self.assertIn("venture prototype", prompt.lower())

        # Direct S7 rule invocation also confirms prompt_only
        s7_direct = self.policy.s7_project_alignment(semester=8, project_topic_unrelated_to_venture=True)
        self.assertTrue(s7_direct["triggered"])
        self.assertTrue(s7_direct["prompt_only"])
        self.assertNotIn("blocked_milestones", s7_direct)

if __name__ == "__main__":
    unittest.main()
