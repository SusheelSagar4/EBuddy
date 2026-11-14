import os
import sys
import csv
import unittest

sys.path.insert(0, os.path.abspath("."))
from typing import List, Dict, Any
from app.kb.core_to_core_repo import core_kb_repo
from app.engine.budget import budget_engine
from app.engine.readiness_gate import readiness_gate_engine
from app.engine.faculty_matcher import faculty_matcher_engine
from app.engine.weekly_guidance import weekly_guidance_engine
from app.services.approach_service import approach_service
from app.services.paper_reader_service import paper_reader_service
from app.services.project_kickoff_service import project_kickoff_service
from app.contracts.student import StudentProfile, SkillState, EvidenceItem
from app.contracts.core_to_core import ReflectionSubmission
from datetime import datetime

class TestCoreToCore(unittest.TestCase):
    """
    Comprehensive Test Suite for Core to Core Feature.
    Covers data integrity, deterministic budget & calendar engine, readiness gate,
    faculty matching, approach assist, paper insights, project kickoff, and simulations.
    """

    def test_01_seed_files_presence_and_data_quality(self):
        """Verify all 11 seed files exist, are strictly verified, and contain zero unverified SAMPLE- rows."""
        seed_dir = "data/seed/core_to_core"
        expected_files = [
            "academic_calendar.csv", "research_areas.csv", "area_skills.csv",
            "faculty.csv", "faculty_areas.csv", "papers.csv", "paper_authors.csv",
            "paper_chunks.csv", "paper_skills.csv", "taster_tasks.csv", "industry_milestones.csv"
        ]
        for fn in expected_files:
            fpath = os.path.join(seed_dir, fn)
            self.assertTrue(os.path.exists(fpath), f"Seed file missing: {fpath}")

        # Check faculty: exactly 44 verified IIT BBS faculty (27 EE, 17 MM)
        self.assertEqual(len(core_kb_repo.faculty), 44)
        for fac in core_kb_repo.faculty.values():
            self.assertTrue(fac.verified)
            self.assertFalse(fac.name.startswith("SAMPLE-"), "Verified seed must not contain SAMPLE- faculty")
            self.assertTrue(fac.profile_url.startswith("https://www.iitbbs.ac.in"))

        # Check papers: exactly 120 verified papers, non-OA have empty fulltext_path
        self.assertEqual(len(core_kb_repo.papers), 120)
        oa_count = 0
        for p in core_kb_repo.papers.values():
            self.assertTrue(p.verified)
            self.assertFalse(p.title.startswith("SAMPLE-"))
            if p.open_access:
                oa_count += 1
            else:
                self.assertFalse(p.fulltext_path, "Non-open-access papers must not store fulltext_path")
        self.assertGreaterEqual(oa_count, 30, "Expected at least 30 open access papers")

    def test_02_deterministic_budget_and_cgpa_protection(self):
        """Verify free-hours budget calculation, calendar scaling, and CGPA protection."""
        # 1. Contact hours parsing
        hrs_3_1_0 = budget_engine.parse_ltp_contact_hours("3-1-0")
        self.assertEqual(hrs_3_1_0, 4.0)

        # 2. Normal teaching week (factor 1.0) with strong CGPA (8.5)
        res_normal = budget_engine.calculate_weekly_budget(
            declared_hours=15.0,
            enrolled_course_ids=["EE2L001", "EE3L001"],
            week_number=3,
            cgpa=8.5,
            backlogs=0
        )
        self.assertEqual(res_normal["calendar_factor"], 1.0)
        self.assertEqual(res_normal["adjusted_budget_hours"], 15.0)
        self.assertFalse(res_normal["cgpa_protection_active"])

        # 3. Midsem week (week 8, factor 0.4) -> CGPA protection MUST activate
        res_midsem = budget_engine.calculate_weekly_budget(
            declared_hours=15.0,
            enrolled_course_ids=["EE2L001", "EE3L001"],
            week_number=8,
            cgpa=8.5,
            backlogs=0
        )
        self.assertEqual(res_midsem["calendar_factor"], 0.4)
        self.assertEqual(res_midsem["adjusted_budget_hours"], 6.0)
        self.assertTrue(res_midsem["cgpa_protection_active"])
        self.assertGreaterEqual(res_midsem["core_course_hours"], 4.0, "Midsem must prioritize core courses (>=70%)")

        # 4. Low CGPA (6.8 < 7.5) during teaching week -> CGPA protection triggers
        res_low_cgpa = budget_engine.calculate_weekly_budget(
            declared_hours=15.0,
            enrolled_course_ids=["EE2L001", "EE3L001"],
            week_number=3,
            cgpa=6.8,
            backlogs=0
        )
        self.assertTrue(res_low_cgpa["cgpa_protection_active"])
        self.assertIn("CGPA protection", res_low_cgpa["protection_reason"])

    def test_03_no_timetable_rule_in_weekly_guidance(self):
        """Verify strict rule: NEVER generate rigid day-by-day or hour-by-hour schedules."""
        states = [
            SkillState(student_id="STU_TEST", skill_id="SKILL_CIRCUIT_ANALYSIS", estimated_level=60.0, confidence=0.8, last_updated=datetime.now()),
            SkillState(student_id="STU_TEST", skill_id="SKILL_POWER_ELECTRONICS", estimated_level=55.0, confidence=0.7, last_updated=datetime.now())
        ]
        plan = weekly_guidance_engine.generate_weekly_focus(
            student_id="STU_TEST",
            programme_id="BTECH_EE",
            declared_hours=15.0,
            enrolled_course_ids=["EE2L001"],
            skill_states=states,
            week_number=2
        )
        self.assertIsInstance(plan.focus_items, list)
        self.assertGreaterEqual(len(plan.focus_items), 2)
        self.assertLessEqual(len(plan.focus_items), 4)

        # Ensure no day names (Monday, Tuesday, etc.) or hour-by-hour slots in activities
        rigid_keywords = ["9:00 AM", "10:00 AM", "Monday:", "Tuesday:", "Hourly Schedule"]
        for it in plan.focus_items:
            for kw in rigid_keywords:
                self.assertNotIn(kw, it.activity)

    def test_04_readiness_gate_never_passes_on_self_declaration(self):
        """Verify readiness gate rejects purely self-declared evidence, requiring objective evidence."""
        # Case 1: Self-declared only evidence
        self_declared_ev = [
            EvidenceItem(
                evidence_id="EV_SELF_01",
                student_id="STU_01",
                skill_id="SKILL_CIRCUIT_ANALYSIS",
                source_type="self_declaration",
                score=95.0,
                recorded_at=datetime.now()
            )
        ]
        states_self = [
            SkillState(student_id="STU_01", skill_id="SKILL_CIRCUIT_ANALYSIS", estimated_level=95.0, confidence=0.2, last_updated=datetime.now())
        ]
        gate_res_fail = readiness_gate_engine.evaluate_gate(
            student_id="STU_01",
            target_area_id="AREA_EE_POWER_SYS",
            skill_states=states_self,
            evidence_ledger=self_declared_ev
        )
        self.assertFalse(gate_res_fail.passed, "Readiness gate must NOT pass on self-declared evidence alone")

        # Case 2: Full compliance with tested skills, 2 tasters, 1 paper summary
        verified_ev = [
            EvidenceItem(
                evidence_id="EV_TEST_01",
                student_id="STU_02",
                skill_id="SKILL_CIRCUIT_ANALYSIS",
                source_type="quiz",
                score=85.0,
                recorded_at=datetime.now()
            ),
            EvidenceItem(
                evidence_id="EV_TEST_02",
                student_id="STU_02",
                skill_id="SKILL_POWER_SYSTEMS",
                source_type="course_grade",
                score=80.0,
                recorded_at=datetime.now()
            )
        ]
        states_ok = [
            SkillState(student_id="STU_02", skill_id="SKILL_CIRCUIT_ANALYSIS", estimated_level=85.0, confidence=0.8, last_updated=datetime.now()),
            SkillState(student_id="STU_02", skill_id="SKILL_POWER_SYSTEMS", estimated_level=80.0, confidence=0.8, last_updated=datetime.now())
        ]
        tasters = [{"task_id": "T1", "score": 75.0}, {"task_id": "T2", "score": 85.0}]
        papers = [{"paper_id": "P1", "score": 80.0}]

        gate_res_pass = readiness_gate_engine.evaluate_gate(
            student_id="STU_02",
            target_area_id="AREA_EE_POWER_SYS",
            skill_states=states_ok,
            evidence_ledger=verified_ev,
            completed_taster_tasks=tasters,
            completed_paper_summaries=papers
        )
        self.assertTrue(gate_res_pass.passed, "Gate should pass when tested mastery >= 0.75, 2 tasters >= 60%, 1 paper >= 60%")

    def test_05_faculty_matcher_ranking_and_grounding(self):
        """Verify deterministic ranking formula, verified faculty citations, and score breakdown."""
        states = [
            SkillState(student_id="STU_EE", skill_id="SKILL_POWER_SYSTEMS", estimated_level=85.0, confidence=0.8, last_updated=datetime.now()),
            SkillState(student_id="STU_EE", skill_id="SKILL_POWER_ELECTRONICS", estimated_level=80.0, confidence=0.8, last_updated=datetime.now())
        ]
        matches = faculty_matcher_engine.rank_faculty(
            student_department="BTECH_EE",
            target_area_ids=["AREA_EE_POWER_SYS", "AREA_EE_POWER_ELEC"],
            skill_states=states,
            top_k=5
        )
        self.assertEqual(len(matches), 5)
        # Scores must be sorted descending
        for i in range(len(matches) - 1):
            self.assertGreaterEqual(matches[i].match_score, matches[i+1].match_score)

        top_match = matches[0]
        self.assertIn("area_similarity", top_match.score_breakdown)
        self.assertIn("skill_fit", top_match.score_breakdown)
        self.assertIn("ug_availability", top_match.score_breakdown)
        self.assertIn("publication_recency", top_match.score_breakdown)
        # Never fabricate faculty: id must exist in verified faculty repository
        self.assertIn(top_match.faculty_id, core_kb_repo.faculty)
        # Stored cited papers must exist in papers repository
        for cp in top_match.cited_papers:
            self.assertIn(cp["paper_id"], core_kb_repo.papers)

    def test_06_approach_assist_rules_and_followup(self):
        """Verify approach draft includes non-contact notice, verified CV bullets, and 10-day follow-up logic."""
        student = StudentProfile(
            student_id="STU_APPROACH_01",
            name="Aarav Sharma",
            programme_id="BTECH_EE",
            current_semester=5,
            cgpa=8.6
        )
        states = [
            SkillState(student_id="STU_APPROACH_01", skill_id="SKILL_POWER_SYSTEMS", estimated_level=85.0, confidence=0.8, last_updated=datetime.now())
        ]
        fac_id = list(core_kb_repo.faculty.keys())[0]

        draft = approach_service.generate_approach_package(
            student=student,
            faculty_id=fac_id,
            skill_states=states,
            available_hours_weekly=12.0
        )
        # Hard Rule: Buddy never contacts professor
        self.assertIn("The buddy never contacts faculty on your behalf", draft.draft_email)
        self.assertEqual(len(draft.interview_questions), 5)
        self.assertEqual(draft.status, "drafted")
        self.assertFalse(draft.followup_recommended)

        # Update to 11 days with no reply
        updated = approach_service.update_approach_status(
            student_id="STU_APPROACH_01",
            faculty_id=fac_id,
            status="sent",
            days_since_sent=11
        )
        self.assertTrue(updated.followup_recommended, "Should flag follow-up recommendation when sent and days >= 10")

    def test_07_paper_reader_open_access_compliance(self):
        """Verify Open Access chunks vs non-Open Access abstract-only compliance."""
        # Find 1 OA paper and 1 non-OA paper
        oa_paper = next(p for p in core_kb_repo.papers.values() if p.open_access)
        non_oa_paper = next(p for p in core_kb_repo.papers.values() if not p.open_access)

        insights_oa = paper_reader_service.get_paper_insights(oa_paper.id)
        self.assertTrue(insights_oa["open_access"])
        self.assertGreaterEqual(len(insights_oa["glossary"]), 2)
        self.assertEqual(len(insights_oa["comprehension_quiz"]), 2)

        insights_non_oa = paper_reader_service.get_paper_insights(non_oa_paper.id)
        self.assertFalse(insights_non_oa["open_access"])
        # Non-OA must have notice
        self.assertIn("Per academic data ethics guidelines", insights_non_oa["annotated_sections"][0]["notice"])

    def test_08_core_industry_roadmap(self):
        """Verify core-industry branch milestones: GATE route, tools, project clubs, core internships."""
        ee_industry = project_kickoff_service.get_industry_roadmap("BTECH_EE")
        self.assertEqual(ee_industry["department"], "EE")
        self.assertGreaterEqual(len(ee_industry["gate_preparation_phases"]), 2)
        self.assertGreaterEqual(len(ee_industry["simulation_and_design_tools"]), 2)
        self.assertGreaterEqual(len(ee_industry["core_internships_and_psus"]), 1)

if __name__ == "__main__":
    unittest.main()
