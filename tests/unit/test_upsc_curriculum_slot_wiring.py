import os
import unittest
from app.personas.registry import persona_registry
from app.personas.btech_upsc.policy import CustomPersonaPolicy

class TestUPSCCurriculumSlotWiring(unittest.TestCase):
    """
    Task 4 Unit Tests: Validates curriculum slot wiring, heavy/light slot classification,
    track resolution (NEP vs 2016-17 per facts.csv F21), and optional subject recommendations.
    """
    @classmethod
    def setUpClass(cls):
        persona_registry.discover()
        pkg = persona_registry.get("btech_upsc")
        cls.policy: CustomPersonaPolicy = pkg.policy

    def test_01_track_resolution_from_f21(self):
        """F21 track rule: Sem 1-4 use NEP, Sem 5-8 use 2016-17 pre-NEP."""
        slots_sem1 = self.policy.get_curriculum_slots("BTECH_EE", 1)
        self.assertEqual(slots_sem1["track"], "NEP")

        slots_sem3 = self.policy.get_curriculum_slots("BTECH_EE", 3)
        self.assertEqual(slots_sem3["track"], "NEP")

        slots_sem5 = self.policy.get_curriculum_slots("BTECH_EE", 5)
        self.assertEqual(slots_sem5["track"], "2016-17")

        slots_sem7 = self.policy.get_curriculum_slots("BTECH_EE", 7)
        self.assertEqual(slots_sem7["track"], "2016-17")

        slots_sem8 = self.policy.get_curriculum_slots("BTECH_EE", 8)
        self.assertEqual(slots_sem8["track"], "2016-17")

    def test_02_ee_slot_classification_heavy_vs_light(self):
        """Verify heavy (Core/Lab) vs light (Breadth/Seminar) slot separation for EE."""
        res_sem3 = self.policy.get_curriculum_slots("BTECH_EE", 3, track="2016-17")
        self.assertGreater(len(res_sem3["heavy_slots"]), 0)
        self.assertGreater(len(res_sem3["light_slots"]), 0)

        heavy_titles = [s.get("course_title", "").lower() for s in res_sem3["heavy_slots"]]
        light_titles = [s.get("course_title", "").lower() for s in res_sem3["light_slots"]]

        # Labs and core should be in heavy
        self.assertTrue(any("laboratory" in t or "signals" in t or "electronics" in t for t in heavy_titles))
        # Breadth and Seminar should be in light
        self.assertTrue(any("breadth" in t or "seminar" in t for t in light_titles))

    def test_03_mme_slot_classification(self):
        """Verify slot wiring for BTECH_MME."""
        res_mme_sem6 = self.policy.get_curriculum_slots("BTECH_MME", 6, track="2016-17")
        self.assertGreater(res_mme_sem6["total_slots"], 0)
        self.assertEqual(res_mme_sem6["programme"], "BTECH_MME")

        # Academic workload and available UPSC hours must be quantified
        self.assertGreater(res_mme_sem6["estimated_academic_hours"], 0)
        self.assertGreaterEqual(res_mme_sem6["recommended_weekly_upsc_hours"], 6.0)

    def test_04_optional_recommendations_ee(self):
        """Verify that Electrical Engineering is recommended with strong overlap for EE."""
        opt_ee = self.policy.get_optional_recommendations("BTECH_EE")
        self.assertEqual(opt_ee["top_choice"], "Electrical Engineering")
        self.assertEqual(len(opt_ee["strong_overlap"]), 1)
        self.assertEqual(opt_ee["strong_overlap"][0]["optional"], "Electrical Engineering")
        self.assertEqual(opt_ee["strong_overlap"][0]["iitbbs_overlap"], "STRONG")

    def test_05_optional_recommendations_mme(self):
        """Verify optional recommendations for MME flag SME-pending review."""
        opt_mme = self.policy.get_optional_recommendations("BTECH_MME")
        self.assertEqual(len(opt_mme["strong_overlap"]), 0)
        self.assertGreater(len(opt_mme["partial_overlap"]), 0)
        self.assertIn("SME", opt_mme["warning"])

if __name__ == "__main__":
    unittest.main()
