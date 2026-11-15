import os
import unittest
from datetime import date
from app.personas.registry import persona_registry
from app.personas.student_startup.policy import CustomPersonaPolicy

class TestStartupPolicyRules(unittest.TestCase):
    """
    Task 2 & 3 Unit Tests:
    Validates persona registration, fallback goals, and rules S1 through S7
    implemented in app/personas/student_startup/policy.py.
    """
    @classmethod
    def setUpClass(cls):
        persona_registry.discover()
        cls.pkg = persona_registry.get("student_startup")
        assert cls.pkg is not None, "student_startup persona must be registered in persona_registry"
        cls.policy = cls.pkg.policy
        cls.spec = cls.pkg.spec

    def test_00_persona_registration_and_spec(self):
        """Task 2: Verify registration, conformance files, and graceful fallback handling."""
        self.assertEqual(self.spec.persona_id, "student_startup")
        self.assertEqual(self.spec.goal_id, "GOAL_STARTUP_FOUNDER")
        self.assertEqual(self.spec.applicable_programmes, ["BTECH_EE", "BTECH_MM"])
        self.assertEqual(self.spec.target_semester_range, [1, 8])

        # Fallback goals
        self.assertEqual(self.spec.fallback_goals.get("BTECH_EE"), "GOAL_EE_CORE_POWER")
        self.assertEqual(self.spec.fallback_goals.get("BTECH_MM"), "GOAL_FALLBACK_MME_CORE")

        # Conformance files loaded
        self.assertEqual(len(self.pkg.requirements), 10)
        self.assertEqual(len(self.pkg.milestones), 8)
        self.assertEqual(self.pkg.mastery["criteria_id"], "MASTERY_STARTUP_FOUNDER")
        self.assertEqual(self.pkg.diagnostic["blueprint"]["item_counts"], 5)

        # Graceful handling of missing fallback persona (GOAL_FALLBACK_MME_CORE is an upstream stub)
        mme_fallback = persona_registry.get("mme_core")
        self.assertIsNone(mme_fallback, "mme_core is an unfulfilled upstream stub and should not exist in registry yet")
        # Ensure policy handles this without crashing
        res_mme = self.policy.s2_cgpa_guard(cgpa=6.3, semester=4, programme="BTECH_MM")
        self.assertTrue(res_mme["triggered"])
        self.assertEqual(res_mme["fallback_goal"], "GOAL_FALLBACK_MME_CORE")
        self.assertTrue(res_mme["fallback_is_stub"])

    def test_01_s1_exam_weeks_pause(self):
        """Rule S1: (a) S1 triggers when end-sem is within 14 days using shared institute_calendar.csv."""
        # Date 2026-11-15: Autumn 2026-27 end_sem starts 2026-11-23 (8 days away <= 14d limit)
        res_cal = self.policy.s1_exam_weeks_pause(current_date="2026-11-15")
        self.assertTrue(res_cal["triggered"], "S1 should trigger 8 days before end_sem")
        self.assertEqual(res_cal["action"], "pause_new_build")
        self.assertIn("weekly_customer_call", res_cal["keep_tasks"])
        self.assertIn("1hr_sprint_review", res_cal["keep_tasks"])
        self.assertEqual(res_cal["shift_milestone_weeks"], 1)

        # Mid-sem within 7 days (Autumn mid_sem is 2026-09-16; check on 2026-09-11 -> 5 days away)
        res_mid = self.policy.s1_exam_weeks_pause(current_date="2026-09-11")
        self.assertTrue(res_mid["triggered"], "S1 should trigger 5 days before mid_sem")

        # Normal instruction day far from exams (2026-08-05) -> should NOT trigger
        res_normal = self.policy.s1_exam_weeks_pause(current_date="2026-08-05")
        self.assertFalse(res_normal["triggered"], "S1 should not trigger when exams are far away")

        # Direct boolean overrides
        self.assertTrue(self.policy.s1_exam_weeks_pause(end_sem_within_14d=True)["triggered"])
        self.assertTrue(self.policy.s1_exam_weeks_pause(mid_sem_within_7d=True)["triggered"])

    def test_02_s2_cgpa_guard(self):
        """Rule S2: (b) S2 with CGPA 6.4 caps weekly hours at 6 (3 in Sem 1-2)."""
        # Sem 3 EE student with CGPA 6.4 -> capped at 6 hr/wk
        res_sem3 = self.policy.s2_cgpa_guard(cgpa=6.4, semester=3, programme="BTECH_EE")
        self.assertTrue(res_sem3["triggered"])
        self.assertEqual(res_sem3["capped_weekly_hours"], 6)
        self.assertTrue(res_sem3["freeze_spending"])
        self.assertEqual(res_sem3["fallback_goal"], "GOAL_EE_CORE_POWER")

        # Sem 1 EE student with CGPA 6.4 -> capped at 3 hr/wk
        res_sem1 = self.policy.s2_cgpa_guard(cgpa=6.4, semester=1, programme="BTECH_EE")
        self.assertTrue(res_sem1["triggered"])
        self.assertEqual(res_sem1["capped_weekly_hours"], 3)

        # Sem 2 MM student with CGPA 6.2 -> capped at 3 hr/wk, MM fallback
        res_sem2_mm = self.policy.s2_cgpa_guard(cgpa=6.2, semester=2, programme="BTECH_MM")
        self.assertTrue(res_sem2_mm["triggered"])
        self.assertEqual(res_sem2_mm["capped_weekly_hours"], 3)
        self.assertEqual(res_sem2_mm["fallback_goal"], "GOAL_FALLBACK_MME_CORE")

        # Triggers on CGPA drop >= 0.3 even with CGPA >= 6.5
        res_drop = self.policy.s2_cgpa_guard(cgpa=7.2, semester=4, cgpa_drop_last_sem=0.35, programme="BTECH_EE")
        self.assertTrue(res_drop["triggered"])

        # Triggers on active backlog even with high CGPA
        res_backlog = self.policy.s2_cgpa_guard(cgpa=8.0, semester=5, active_backlogs=1, programme="BTECH_EE")
        self.assertTrue(res_backlog["triggered"])

        # Regular standing (CGPA 8.0, 0 backlogs, 0 drop) -> not triggered
        res_ok = self.policy.s2_cgpa_guard(cgpa=8.0, semester=5, programme="BTECH_EE")
        self.assertFalse(res_ok["triggered"])

    def test_03_s3_validation_gate(self):
        """Rule S3: (c) S3 blocks MVP work when fewer than 10 interviews are logged."""
        # Fewer than 10 interviews on startup_team_and_mvp milestone -> triggered
        res_blocked = self.policy.s3_validation_gate(interviews_logged=8, milestone="startup_team_and_mvp")
        self.assertTrue(res_blocked["triggered"])
        self.assertTrue(res_blocked["block_mvp_spend"])
        self.assertTrue(res_blocked["block_feature_work"])
        self.assertEqual(res_blocked["forced_milestone"], "startup_problem_validation")
        self.assertEqual(res_blocked["min_interviews_required"], 10)

        # 10 or more interviews logged -> not triggered
        res_ok = self.policy.s3_validation_gate(interviews_logged=10, milestone="startup_team_and_mvp")
        self.assertFalse(res_ok["triggered"])

        # 15 interviews logged -> not triggered
        res_plenty = self.policy.s3_validation_gate(interviews_logged=15, milestone="startup_team_and_mvp")
        self.assertFalse(res_plenty["triggered"])

        # On other milestones (e.g. startup_orientation_log), S3 does not block
        res_other = self.policy.s3_validation_gate(interviews_logged=2, milestone="startup_orientation_log")
        self.assertFalse(res_other["triggered"])

    def test_04_s4_runway_guard(self):
        """Rule S4: (d) S4 triggers at runway under 3 months."""
        # Runway 2.2 months and active burn -> triggered
        res_runway = self.policy.s4_runway_guard(runway_months=2.2, monthly_burn=15000.0)
        self.assertTrue(res_runway["triggered"])
        self.assertTrue(res_runway["block_new_spend"])
        self.assertIn("cut_cost", res_runway["options"])
        self.assertIn("seek_grant_incubation", res_runway["options"])
        self.assertIn("SR08", res_runway["recommended_resources"])
        self.assertIn("SR09", res_runway["recommended_resources"])

        # Check Hard Rule 3: Links official pages with "check the official page", never states amounts/fees
        for link_info in res_runway["resource_links"]:
            self.assertEqual(link_info["note"], "check the official page")
            self.assertTrue(link_info["url"].startswith("https://"))

        # Runway >= 3 months -> not triggered
        res_ok = self.policy.s4_runway_guard(runway_months=4.5, monthly_burn=15000.0)
        self.assertFalse(res_ok["triggered"])

        # Monthly burn == 0 -> not triggered
        res_no_burn = self.policy.s4_runway_guard(runway_months=1.0, monthly_burn=0.0)
        self.assertFalse(res_no_burn["triggered"])

    def test_05_s5_ip_before_disclosure(self):
        """Rule S5: IP check task inserted before public demo."""
        # Public demo planned with unchecked IP status -> triggered
        res = self.policy.s5_ip_before_disclosure(public_demo_planned=True, ip_status="unchecked")
        self.assertTrue(res["triggered"])
        self.assertEqual(res["action"], "insert_ip_check_task")
        self.assertEqual(res["recommended_resource"], "SR07")
        self.assertTrue(res["requires_institute_ip_policy_review"])

        # Check Hard Rule 5: NPTEL resource states "check the course page for the next run"
        self.assertIn("check the course page for the next run", res["resource_detail"]["note"])

        # Already checked IP status -> not triggered
        res_checked = self.policy.s5_ip_before_disclosure(public_demo_planned=True, ip_status="checked")
        self.assertFalse(res_checked["triggered"])

        # No demo planned -> not triggered
        res_no_demo = self.policy.s5_ip_before_disclosure(public_demo_planned=False, ip_status="unchecked")
        self.assertFalse(res_no_demo["triggered"])

    def test_06_s6_placement_interplay(self):
        """Rule S6: (e) S6 keeps the 5 hr/week floor in Sem 7 when placement_registered is true."""
        # Sem 7 with placement_registered = True -> triggered
        res_sem7 = self.policy.s6_placement_interplay(semester=7, placement_registered=True)
        self.assertTrue(res_sem7["triggered"])
        self.assertEqual(res_sem7["floor_hours"], 5)
        self.assertEqual(res_sem7["sem8_required_milestone"], "startup_traction_decision")

        # Sem 6 with placement_registered = True -> not triggered
        res_sem6 = self.policy.s6_placement_interplay(semester=6, placement_registered=True)
        self.assertFalse(res_sem6["triggered"])

        # Sem 7 with placement_registered = False -> not triggered
        res_no_place = self.policy.s6_placement_interplay(semester=7, placement_registered=False)
        self.assertFalse(res_no_place["triggered"])

    def test_07_s7_project_alignment(self):
        """Rule S7: Sem 7/8 project alignment prompt only."""
        # Sem 8 student with venture-unrelated project -> prompted
        res_sem8 = self.policy.s7_project_alignment(semester=8, project_topic_unrelated_to_venture=True)
        self.assertTrue(res_sem8["triggered"])
        self.assertTrue(res_sem8["prompt_only"])
        self.assertIn("aligning", res_sem8["prompt"].lower())
        self.assertIn("project guide", res_sem8["prompt"].lower())

        # Sem 7 student with unrelated project -> prompted
        res_sem7 = self.policy.s7_project_alignment(semester=7, project_topic_unrelated_to_venture=True)
        self.assertTrue(res_sem7["triggered"])
        self.assertTrue(res_sem7["prompt_only"])

        # Project already aligned -> not triggered
        res_aligned = self.policy.s7_project_alignment(semester=8, project_topic_unrelated_to_venture=False)
        self.assertFalse(res_aligned["triggered"])

        # Sem 6 (pre-project) -> not triggered
        res_sem6 = self.policy.s7_project_alignment(semester=6, project_topic_unrelated_to_venture=True)
        self.assertFalse(res_sem6["triggered"])

    def test_08_no_hardcoded_parameters(self):
        """Rule parameter integrity: verify all rule parameters are read from policy_rules.yaml."""
        self.assertIn("S1", self.policy.rules_by_id)
        self.assertIn("S2", self.policy.rules_by_id)
        self.assertIn("S3", self.policy.rules_by_id)
        self.assertIn("S4", self.policy.rules_by_id)
        self.assertIn("S6", self.policy.rules_by_id)

        s2_params = self.policy.rules_by_id["S2"]["params"]
        self.assertEqual(s2_params["floor_hard"], 6.5)
        self.assertEqual(s2_params["cap_hours"], 6)
        self.assertEqual(s2_params["cap_hours_sem12"], 3)

        s3_params = self.policy.rules_by_id["S3"]["params"]
        self.assertEqual(s3_params["min_interviews"], 10)

        s4_params = self.policy.rules_by_id["S4"]["params"]
        self.assertEqual(s4_params["min_runway_months"], 3)

        s6_params = self.policy.rules_by_id["S6"]["params"]
        self.assertEqual(s6_params["floor_hours"], 5)

if __name__ == "__main__":
    unittest.main()
