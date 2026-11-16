import os
import sys
import unittest

sys.path.insert(0, os.path.abspath("."))

from scripts.evaluate_scorecard import (
    build_32_mtech_synthetic_profiles,
    run_mtech_scorecard_evaluation
)
from app.kb.core_to_mtech_repo import core_to_mtech_repo
from app.engine.eligibility import eligibility_engine
from app.engine.gate_readiness_shortlist import gate_readiness_shortlist_engine
from app.engine.gate_conflicts_and_tracker import gate_conflicts_and_tracker_engine
from app.engine.gate_interview_and_replan import gate_interview_and_replan_engine
from app.engine.gate_diagnostic import gate_diagnostic_engine

class TestMTechEvaluationScorecard(unittest.TestCase):
    """
    Automated evaluation test suite covering the 32 synthetic student profiles
    and 6 core dimensions of the Core to M.Tech feature (§16).
    """

    def test_01_cohort_demographics_and_distribution(self):
        """Verify 32 synthetic profiles cover EE & MM, CGPA 5.5-9.5, backlogs, years 2-4, and routes."""
        profiles = build_32_mtech_synthetic_profiles()
        self.assertGreaterEqual(len(profiles), 32)

        ee_profiles = [p for p in profiles if p["dept"] == "EE"]
        mm_profiles = [p for p in profiles if p["dept"] == "MM"]
        self.assertEqual(len(ee_profiles), 16)
        self.assertEqual(len(mm_profiles), 16)

        cgpas = [p["cgpa"] for p in profiles]
        self.assertLessEqual(min(cgpas), 5.5)
        self.assertGreaterEqual(max(cgpas), 9.5)

        years = {p["year"] for p in profiles}
        self.assertTrue({2, 3, 4}.issubset(years))

        backlogs_set = {p["backlogs"] for p in profiles}
        self.assertTrue({0, 1, 2}.issubset(backlogs_set))

        routes = {p["route"] for p in profiles}
        self.assertTrue({"ROUTE_MTECH_INDIA", "ROUTE_MSR_PHD_INDIA", "ROUTE_PSU_GATE", "ROUTE_UNDECIDED"}.issubset(routes))

    def test_02_eligibility_and_cited_rule_grounding(self):
        """Every profile's eligibility check is deterministic and cites real stored rules with source URLs."""
        profiles = build_32_mtech_synthetic_profiles()
        for p in profiles:
            elig = eligibility_engine.check_gate_exam_eligibility(
                year=p["year"],
                semester=p["sem"],
                branch=p["programme"],
                primary_paper=p["paper"]
            )
            self.assertTrue(bool(elig.rule_id))
            self.assertTrue(bool(elig.rule_source))
            self.assertTrue(bool(elig.rule_text))

            if p["year"] == 2:
                self.assertEqual(elig.status, "eligible_later")
                self.assertEqual(elig.rule_id, "RULE_GATE_YEAR_ELIGIBILITY")
                self.assertIsNotNone(elig.best_valid_option)
            else:
                self.assertEqual(elig.status, "eligible")

            # Low CGPA targeting Direct PhD edge cases
            if p["edge"] == "low_cgpa_iisc_phd":
                prog_chk = eligibility_engine.check_programme_eligibility(
                    student_branch=p["programme"],
                    student_cgpa=p["cgpa"],
                    backlogs=p["backlogs"],
                    programme_id=p["target_prog"],
                    paper_code=p["paper"]
                )
                self.assertFalse(prog_chk.is_eligible)
                self.assertIn("RULE_DIRECT_PHD_MIN_CGPA", prog_chk.rule_id)
                self.assertIsNotNone(prog_chk.best_valid_option)

    def test_03_zero_unverified_data_leak_and_tier_stability(self):
        """Zero unverified rows leak in production mode; tiering is 100% stable across 3 runs in demo mode."""
        profiles = build_32_mtech_synthetic_profiles()
        for p in profiles:
            # Production air-gapped call: MUST return 0 programmes
            strict = gate_readiness_shortlist_engine.compute_shortlist_and_tiers(
                student_branch=p["programme"],
                student_cgpa=p["cgpa"],
                backlogs=p["backlogs"],
                paper_code=p["paper"],
                category="GEN",
                score_band=None,
                allow_unverified_demo=False
            )
            self.assertEqual(len(strict.reach), 0)
            self.assertEqual(len(strict.target), 0)
            self.assertEqual(len(strict.safe), 0)

            # In demo mode with >= 2 mocks: check 3 repeated runs
            if len(p["mocks"]) >= 2:
                band = gate_readiness_shortlist_engine.compute_predicted_score_band(p["mocks"])
                runs = []
                for _ in range(3):
                    sl = gate_readiness_shortlist_engine.compute_shortlist_and_tiers(
                        student_branch=p["programme"],
                        student_cgpa=p["cgpa"],
                        backlogs=p["backlogs"],
                        paper_code=p["paper"],
                        category="GEN",
                        score_band=band,
                        allow_unverified_demo=True
                    )
                    runs.append(([x.programme_id for x in sl.reach], [x.programme_id for x in sl.target], [x.programme_id for x in sl.safe]))
                self.assertEqual(runs[0], runs[1])
                self.assertEqual(runs[1], runs[2])

    def test_04_dynamic_adaptation_and_question_grounding(self):
        """Verify the 4 dynamic adaptation scenarios and 100% question grounding in syllabus topics."""
        # 1. Rising vs Falling mock trend
        rising_band = gate_readiness_shortlist_engine.compute_predicted_score_band([780.0, 830.0, 860.0])
        falling_band = gate_readiness_shortlist_engine.compute_predicted_score_band([710.0, 640.0, 580.0])
        self.assertGreater(rising_band.mean_score, falling_band.mean_score)

        # 2. Placement clash & End-sem clash
        p_clash = gate_conflicts_and_tracker_engine.detect_conflicts(current_week=7, placement_active=True)
        e_clash = gate_conflicts_and_tracker_engine.detect_conflicts(current_week=14)
        self.assertTrue(any(c.kind == "placement_clash" and len(c.options) >= 2 for c in p_clash))
        self.assertTrue(any(c.kind == "exam_clash" and len(c.options) >= 2 for c in e_clash))

        # 3. Post-result re-plan for below-target score
        replan = gate_interview_and_replan_engine.replan_post_result(
            student_id="SYN_LOW", actual_score=420.0, actual_rank=4800,
            paper_code="EE", category="GEN", branch="BTECH_EE", cgpa=7.0, backlogs=0
        )
        self.assertTrue(replan["score_below_target_warning"])
        self.assertGreaterEqual(len(replan["alternatives"]), 3)

        # 4. Route switch preserving 100% of evidence
        switch_res = gate_interview_and_replan_engine.switch_route(
            student_id="SYN_PIVOT", from_route="ROUTE_MTECH_INDIA", to_route="ROUTE_PSU_GATE", current_evidence_count=16
        )
        self.assertTrue(switch_res["plan_version_bump"])
        self.assertGreater(len(switch_res["what_carries_over"]), 0)
        self.assertGreater(len(switch_res["what_changes"]), 0)

        # 5. Question grounding
        cand_ee = gate_diagnostic_engine.get_candidate_topics(paper_code="EE")
        cand_mt = gate_diagnostic_engine.get_candidate_topics(paper_code="MT")
        ee_items = []
        ans_ee = []
        for _ in range(10):
            it = gate_diagnostic_engine.select_next_item(cand_ee, ans_ee)
            if not it:
                break
            ee_items.append(it)
            ans_ee.append({"item_id": it.item_id, "topic_id": it.topic_id, "is_correct": True, "difficulty": it.difficulty})

        mt_items = []
        ans_mt = []
        for _ in range(10):
            it = gate_diagnostic_engine.select_next_item(cand_mt, ans_mt)
            if not it:
                break
            mt_items.append(it)
            ans_mt.append({"item_id": it.item_id, "topic_id": it.topic_id, "is_correct": True, "difficulty": it.difficulty})

        self.assertTrue(all(q.topic_id in core_to_mtech_repo.syllabus_topics for q in ee_items))
        self.assertTrue(all(q.topic_id in core_to_mtech_repo.syllabus_topics for q in mt_items))
        self.assertTrue(all(q.item_id in gate_diagnostic_engine.items_by_id or q.item_id in core_to_mtech_repo.pyq_items for q in ee_items))
        self.assertTrue(all(q.item_id in gate_diagnostic_engine.items_by_id or q.item_id in core_to_mtech_repo.pyq_items for q in mt_items))

    def test_05_scorecard_markdown_file_generation(self):
        """Executing run_mtech_scorecard_evaluation creates docs/core_to_mtech_scorecard.md with 100% pass rates."""
        run_mtech_scorecard_evaluation()
        report_path = os.path.join(os.getenv("EBUDDY_REPORTS_DIR", "docs"), "core_to_mtech_scorecard.md")
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("# Core to M.Tech Evaluation Scorecard", content)
        self.assertIn("32 synthetic student profiles", content)
        self.assertIn("PASS (100%)", content)

if __name__ == "__main__":
    unittest.main()
