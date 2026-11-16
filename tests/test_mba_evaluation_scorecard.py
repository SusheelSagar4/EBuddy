import os
import sys
import unittest

sys.path.insert(0, os.path.abspath("."))
from scripts.evaluate_mba_scorecard import build_32_synthetic_mba_profiles, run_mba_scorecard_evaluation

class TestMBAEvaluationScorecard(unittest.TestCase):
    """
    Verification Test for Core to MBA Scorecard Evaluation over 32 Synthetic Profiles.
    """

    def test_scorecard_32_profiles_and_report_generation(self):
        profiles = build_32_synthetic_mba_profiles()
        self.assertEqual(len(profiles), 32)
        
        ee_profiles = [p for p in profiles if p["dept"] == "EE"]
        mm_profiles = [p for p in profiles if p["dept"] == "MM"]
        self.assertEqual(len(ee_profiles), 16)
        self.assertEqual(len(mm_profiles), 16)

        # Execute scorecard evaluation
        run_mba_scorecard_evaluation()

        report_path = os.path.join(os.getenv("EBUDDY_REPORTS_DIR", "docs"), "core_to_mba_scorecard.md")
        self.assertTrue(os.path.exists(report_path), "Scorecard markdown report must be written to docs/core_to_mba_scorecard.md")
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("100.0%", content)
        self.assertIn("Zero Rigid Timetable Guarantee", content)
        self.assertIn("CGPA Protection", content)
        self.assertIn("Verbal-Gap Protocol Activation", content)
        self.assertIn("Empirical Mock Calibration Rule", content)
        self.assertIn("Zero-Leak Guarantee", content)
        self.assertIn("Lateral Switch-Back with 100% Evidence Preservation", content)

if __name__ == "__main__":
    unittest.main()
