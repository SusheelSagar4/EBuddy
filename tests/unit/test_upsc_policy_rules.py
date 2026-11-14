import os
import unittest
from datetime import date
from app.personas.registry import persona_registry
from app.personas.btech_upsc.policy import CustomPersonaPolicy

class TestUPSCPolicyRules(unittest.TestCase):
    """
    Task 3 Unit Tests: Validates rules R1 through R10 implemented in
    app/personas/btech_upsc/policy.py.
    """
    @classmethod
    def setUpClass(cls):
        persona_registry.discover()
        pkg = persona_registry.get("btech_upsc")
        cls.policy: CustomPersonaPolicy = pkg.policy
        cls.spec = pkg.spec

    def test_01_r01_workload_overload(self):
        """Rule R1: Workload overload in Sem 6/7 shifts milestones and pauses optional."""
        # Sem 6 with heavy workload (< 10 hrs available)
        res = self.policy.r1_workload_overload(semester=6, weekly_hours_available=8.0)
        self.assertTrue(res["triggered"])
        self.assertEqual(res["action"], "pause_optional_and_static")
        self.assertIn("SKILL_UPSC_OPTIONAL", res["pause_skills"])
        self.assertEqual(res["shift_milestone_weeks"], 1)
        self.assertFalse(res["mark_milestone_failed"])
        self.assertEqual(res["answers_per_day"], 2)

        # Sem 6 with very low hours (< 6 hrs available) -> 1 answer/day
        res_low = self.policy.r1_workload_overload(semester=6, weekly_hours_available=5.0)
        self.assertTrue(res_low["triggered"])
        self.assertEqual(res_low["answers_per_day"], 1)

        # Sem 4 should not trigger R1 even if hours are low
        res_sem4 = self.policy.r1_workload_overload(semester=4, weekly_hours_available=5.0)
        self.assertFalse(res_sem4["triggered"])

    def test_02_r02_cgpa_guard(self):
        """Rule R2: (b) CGPA 6.4 (< 6.5 floor) caps weekly UPSC hours and routes to fallback."""
        res = self.policy.r2_cgpa_guard(student_cgpa=6.4, semester=5, programme="BTECH_EE")
        self.assertTrue(res["triggered"])
        self.assertEqual(res["capped_weekly_hours"], 6)
        self.assertIn("upsc_summer_intensive_y3", res["blocked_milestones"])
        self.assertIn("upsc_prelims_mock_phase", res["blocked_milestones"])
        self.assertEqual(res["fallback_goal"], "GOAL_EE_CORE_POWER")

        # In Sem 1-2, cap is 3 hours
        res_sem1 = self.policy.r2_cgpa_guard(student_cgpa=6.2, semester=1, programme="BTECH_EE")
        self.assertTrue(res_sem1["triggered"])
        self.assertEqual(res_sem1["capped_weekly_hours"], 3)

        # MME programme routes to MME fallback
        res_mme = self.policy.r2_cgpa_guard(student_cgpa=6.3, semester=4, programme="BTECH_MME")
        self.assertTrue(res_mme["triggered"])
        self.assertEqual(res_mme["fallback_goal"], "GOAL_FALLBACK_MME_CORE")

        # Regular standing (CGPA 8.0, 0 backlogs) does not trigger R2
        res_ok = self.policy.r2_cgpa_guard(student_cgpa=8.0, semester=5, programme="BTECH_EE")
        self.assertFalse(res_ok["triggered"])

    def test_03_r03_optional_gate(self):
        """Rule R3: Optional subject must be locked in by Sem 5 (EE) or Sem 6 (MME)."""
        # Sem 5 EE with no optional chosen -> triggered
        res_ee = self.policy.r3_optional_gate(semester=5, optional_chosen=None, programme="BTECH_EE")
        self.assertTrue(res_ee["triggered"])
        self.assertIn("SKILL_UPSC_OPTIONAL", res_ee["blocked_skills"])
        self.assertEqual(res_ee["forced_milestone"], "upsc_optional_lock_in")
        self.assertEqual(res_ee["recommended_optional"], "Electrical Engineering")

        # Sem 6 MME with undecided optional -> triggered
        res_mme = self.policy.r3_optional_gate(semester=6, optional_chosen="undecided", programme="BTECH_MME")
        self.assertTrue(res_mme["triggered"])
        self.assertIn("SME-pending", res_mme["warning"])

        # Sem 4 EE (before deadline) -> not triggered
        res_sem4 = self.policy.r3_optional_gate(semester=4, optional_chosen=None, programme="BTECH_EE")
        self.assertFalse(res_sem4["triggered"])

    def test_04_r04_baseline_gate(self):
        """Rule R4: NCERT completion below 80% in Sem 3+ blocks static pass 1."""
        res_low = self.policy.r4_baseline_gate(semester=3, ncert_completion=0.65)
        self.assertTrue(res_low["triggered"])
        self.assertIn("upsc_static_pass1", res_low["blocked_milestones"])
        self.assertEqual(res_low["forced_milestone"], "upsc_ncert_baseline")

        # Adequate completion (85%) does not trigger gate
        res_ok = self.policy.r4_baseline_gate(semester=3, ncert_completion=0.85)
        self.assertFalse(res_ok["triggered"])

    def test_05_r05_csat_remediation(self):
        """Rule R5: CSAT score below 80 within 16 weeks of Prelims adds 4 hrs/wk drills."""
        res = self.policy.r5_csat_remediation(csat_avg_last3=74.5, weeks_to_prelims=12)
        self.assertTrue(res["triggered"])
        self.assertEqual(res["remediation_hours_per_week"], 4)
        self.assertEqual(res["max_answers_per_week"], 2)

        # Sufficient score or far out does not trigger
        res_ok_score = self.policy.r5_csat_remediation(csat_avg_last3=85.0, weeks_to_prelims=10)
        self.assertFalse(res_ok_score["triggered"])
        res_ok_weeks = self.policy.r5_csat_remediation(csat_avg_last3=72.0, weeks_to_prelims=24)
        self.assertFalse(res_ok_weeks["triggered"])

    def test_06_r06_placement_interplay(self):
        """Rule R6: Sem 7 placement season interaction and target hours."""
        # Placement active with pending outcome
        res_active = self.policy.r6_placement_interplay(semester=7, placement_registered=True, placement_outcome="pending")
        self.assertTrue(res_active["triggered"])
        self.assertEqual(res_active["target_weekly_hours"], 6)

        # Secured placement offer
        res_offer = self.policy.r6_placement_interplay(semester=7, placement_registered=True, placement_outcome="offer", student_cgpa=7.5)
        self.assertTrue(res_offer["triggered"])
        self.assertEqual(res_offer["target_weekly_hours_sem8"], 20)
        self.assertTrue(res_offer["sem8_attempt_allowed"])

        # No placement offer -> Sem 8 target 25 hrs, deferral recommended
        res_no_offer = self.policy.r6_placement_interplay(semester=7, placement_registered=True, placement_outcome="no_offer")
        self.assertTrue(res_no_offer["triggered"])
        self.assertEqual(res_no_offer["target_weekly_hours_sem8"], 25)
        self.assertFalse(res_no_offer["sem8_attempt_allowed"])

    def test_07_r07_attempt_decision(self):
        """Rule R7: (e) Returns 'not confirmed yet' if fewer than 2 verified cut-off cycles exist."""
        res = self.policy.r7_attempt_decision(semester=8, static_pass1_completion=0.7)
        self.assertTrue(res["triggered"])
        self.assertTrue(res["defer_first_attempt"])
        # Exactly 1 verified row exists in cutoffs.csv (CSE-2025), so must return "not confirmed yet"
        self.assertEqual(res["verified_cutoff_cycles_count"], 1)
        self.assertEqual(res["cutoff_benchmark"], "not confirmed yet")
        # Confirms F04 warning is present
        self.assertIn("appears in any one Prelims paper", res["f04_warning"])

    def test_08_r08_late_start(self):
        """Rule R8: (c) Sem 7 student with static_pass1_completion < 0.5 returns attempt-after-graduation default."""
        res_default = self.policy.r8_late_start(semester=7, static_pass1_completion=0.4, weekly_hours_available=10.0)
        self.assertTrue(res_default["triggered"])
        self.assertEqual(res_default["recommendation"], "attempt_after_graduation")

        # Student insists on Sem 8 with >= 15 hrs available -> compressed static sprint
        res_sprint = self.policy.r8_late_start(semester=7, static_pass1_completion=0.4, weekly_hours_available=16.0, student_insists_sem8=True)
        self.assertTrue(res_sprint["triggered"])
        self.assertEqual(res_sprint["recommendation"], "compressed_static_sprint")
        self.assertEqual(res_sprint["sprint_weeks"], 12)

    def test_09_r09_age_eligibility(self):
        """Rule R9: (d) Age check uses facts F01/F02 (min age 21 on 1 August of target year)."""
        # Candidate born 2006-10-15 targeting CSE 2027: Age on 2027-08-01 is 20 (< 21)
        res_underage = self.policy.r9_age_eligibility(birth_date=date(2006, 10, 15), target_exam_year=2027)
        self.assertTrue(res_underage["triggered"]) # Triggered flag means restricted
        self.assertFalse(res_underage["eligible_for_target_year"])
        self.assertEqual(res_underage["age_on_1_august"], 20)
        self.assertEqual(res_underage["earliest_attempt_year"], 2028)

        # Candidate born 2004-05-10 targeting CSE 2027: Age on 2027-08-01 is 23 (>= 21)
        res_eligible = self.policy.r9_age_eligibility(birth_date=date(2004, 5, 10), target_exam_year=2027)
        self.assertFalse(res_underage["eligible_for_target_year"] == res_eligible["eligible_for_target_year"])
        self.assertTrue(res_eligible["eligible_for_target_year"])
        self.assertEqual(res_eligible["earliest_attempt_year"], 2027)

    def test_10_r10_sem8_exam_clash(self):
        """Rule R10: (a) Sem 8 2027: new topics end 2027-04-22, capped hours until viva on 2027-05-19, revision only until Prelims 2027-05-23."""
        res = self.policy.r10_sem8_exam_clash(semester=8, target_attempt_year=2027, current_year=2027)
        self.assertTrue(res["triggered"])
        self.assertEqual(res["new_topics_cutoff_date"], "2027-04-22")
        self.assertEqual(res["clash_window_end"], "2027-05-19")
        self.assertEqual(res["clash_capped_hours"], 10)
        self.assertEqual(res["prelims_date"], "2027-05-23")
        self.assertEqual(res["schedule"]["phase_1_new_topics_end"], "2027-04-22")
        self.assertEqual(res["schedule"]["phase_2_viva_date"], "2027-05-19")
        self.assertEqual(res["schedule"]["phase_3_prelims_date"], "2027-05-23")

if __name__ == "__main__":
    unittest.main()
