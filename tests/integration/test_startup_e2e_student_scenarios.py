import os
import csv
import unittest
from datetime import datetime, timezone
from app.contracts.student import StudentProfile, EvidenceItem
from app.contracts.goal import Goal, GoalRequirement
from app.personas.registry import persona_registry
from app.personas.student_startup.policy import CustomPersonaPolicy
from app.engine.planner import Planner
from app.engine.validator import PlanValidator
from app.engine.gaps import GapAnalyzer
from app.engine.skill_state import SkillStateUpdater

class TestStartupE2EStudentScenarios(unittest.TestCase):
    """
    Task 5 End-to-End Tests:
    Verifies full lifecycle (milestones, rule outputs, 5-item diagnostic from bank,
    curriculum slots, planning, and validation) for:
      (1) Sem 3 EE student
      (2) Sem 6 MME student
      (3) Sem 8 EE student
    """
    @classmethod
    def setUpClass(cls):
        persona_registry.discover()
        cls.pkg = persona_registry.get("student_startup")
        assert cls.pkg is not None, "student_startup persona must be registered"
        cls.policy: CustomPersonaPolicy = cls.pkg.policy
        cls.planner = Planner()
        cls.validator = PlanValidator()
        cls.gap_analyzer = GapAnalyzer()
        cls.state_updater = SkillStateUpdater()

        cls.goal = Goal(
            goal_id=cls.pkg.spec.goal_id,
            name="Student Startup Founder",
            category="startup",
            description=cls.pkg.spec.description,
            source_id="DESIGN_TEAM"
        )
        cls.reqs = [
            GoalRequirement(
                goal_id=cls.goal.goal_id,
                skill_id=r["skill_id"],
                required_level=float(r["required_level"]),
                importance=float(r.get("importance", 1.0)),
                source_id="DESIGN_TEAM"
            )
            for r in cls.pkg.requirements
        ]

        # Load diagnostic item bank
        raw_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "higher_studies", "startup")
        )
        cls.diagnostic_items = []
        with open(os.path.join(raw_dir, "diagnostic_items.csv"), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cls.diagnostic_items = list(reader)

    def test_01_sem3_ee_student(self):
        """
        Scenario 1: Sem 3 EE student.
        - Problem validation milestone.
        - 5-item diagnostic assessment from bank.
        - Rules: S1 exam weeks pause, S2 CGPA guard, S3 validation gate.
        - Plan generation & validation passed.
        """
        student = StudentProfile(
            student_id="STU_STARTUP_EE_SEM3",
            name="Aarav Sharma",
            programme_id="BTECH_EE",
            current_semester=3,
            cgpa=8.2,
            backlogs=0,
            is_synthetic=True
        )

        # 1. 5-item Diagnostic Assessment sampled from diagnostic_items.csv bank
        target_skills = self.pkg.diagnostic["blueprint"]["target_skills"]
        selected_items = []
        for ts in target_skills:
            matching = [it for it in self.diagnostic_items if it["skill_slug"] == ts]
            selected_items.extend(matching[:2])
        selected_items = selected_items[:5]
        self.assertEqual(len(selected_items), 5)

        ev_items = [
            EvidenceItem(
                evidence_id=f"EV_SEM3_{it['item_id']}",
                student_id=student.student_id,
                skill_id=it["skill_slug"],
                source_type="quiz",
                score=70.0 + (i * 4.0),
                recorded_at=datetime.now(timezone.utc)
            )
            for i, it in enumerate(selected_items)
        ]
        self.assertEqual(len(ev_items), 5)
        skill_states = self.state_updater.update_states(student.student_id, ev_items)
        self.assertGreaterEqual(len(skill_states), 1)

        # 2. Milestones verification (Sem 3: startup_problem_validation)
        sem3_milestones = [m for m in self.pkg.milestones if m.get("semester_target") == 3]
        self.assertEqual(len(sem3_milestones), 1)
        self.assertEqual(sem3_milestones[0]["title"], "Problem validation")
        self.assertIn("20 customer interviews", sem3_milestones[0]["description"])

        # 3. Rules: S1, S2, S3
        # S1: check exam pause on date near end-sem (8 days away)
        s1 = self.policy.s1_exam_weeks_pause(current_date="2026-11-15")
        self.assertTrue(s1["triggered"])
        self.assertEqual(s1["action"], "pause_new_build")
        self.assertEqual(s1["shift_milestone_weeks"], 1)

        # S2: CGPA guard with 8.2 -> not triggered
        s2 = self.policy.s2_cgpa_guard(student.cgpa, student.current_semester, programme=student.programme_id)
        self.assertFalse(s2["triggered"])

        # S3: Validation gate blocks MVP feature work if interviews < 10
        s3 = self.policy.s3_validation_gate(interviews_logged=6, milestone="startup_team_and_mvp")
        self.assertTrue(s3["triggered"])
        self.assertTrue(s3["block_mvp_spend"])
        self.assertEqual(s3["forced_milestone"], "startup_problem_validation")

        # 4. Curriculum slot analysis (NEP track from admission year 2025-26)
        slots = self.policy.get_curriculum_slots(student.programme_id, student.current_semester, admission_year="2025-26")
        self.assertEqual(slots["track"], "NEP")

        # 4b. When evaluated against current 2016-17 curriculum table
        slots_curr = self.policy.get_curriculum_slots(student.programme_id, student.current_semester, track="2016-17")
        self.assertGreater(slots_curr["estimated_academic_hours"], 0)
        self.assertGreaterEqual(slots_curr["recommended_weekly_venture_hours"], 5.0)

        # 5. Planning and Validation
        gaps = self.gap_analyzer.analyze_gaps(self.goal, self.reqs, skill_states)
        plan = self.planner.generate_plan(student, self.goal, gaps, [], [])
        report = self.validator.validate_plan(plan, student)
        self.assertTrue(report.passed, f"Validation failed: {report.messages}")
        self.assertGreater(len(plan.items), 0)

        # Confirm verified resource items include NPTEL or portal notices
        res_items = [it for it in plan.items if it.item_type == "resource"]
        self.assertGreater(len(res_items), 0)
        for ri in res_items:
            # Check Hard Rule 5: NPTEL courses check next run
            if "nptel" in ri.reason.why_this.lower():
                self.assertIn("check the course page for the next run", ri.reason.why_this)
            # Check Hard Rule 3: Scheme portals say check the official page
            if "startup india" in ri.reason.why_this.lower() or "rep" in ri.reason.why_this.lower():
                self.assertIn("check the official page", ri.reason.why_this)

    def test_02_sem6_mme_student(self):
        """
        Scenario 2: Sem 6 MME student.
        - Summer pilot milestone.
        - 5-item diagnostic assessment.
        - Rules: S4 runway guard, S5 IP before disclosure, S2 fallback check.
        - Plan generation & validation passed.
        """
        student = StudentProfile(
            student_id="STU_STARTUP_MME_SEM6",
            name="Ananya Mishra",
            programme_id="BTECH_MM",
            current_semester=6,
            cgpa=7.5,
            backlogs=0,
            is_synthetic=True
        )

        # 1. 5-item Diagnostic Assessment from bank
        selected_items = self.diagnostic_items[5:10]
        self.assertEqual(len(selected_items), 5)
        ev_items = [
            EvidenceItem(
                evidence_id=f"EV_SEM6_{it['item_id']}",
                student_id=student.student_id,
                skill_id=it["skill_slug"],
                source_type="quiz",
                score=68.0 + (i * 5.0),
                recorded_at=datetime.now(timezone.utc)
            )
            for i, it in enumerate(selected_items)
        ]
        skill_states = self.state_updater.update_states(student.student_id, ev_items)

        # 2. Milestones verification (Sem 6: Summer pilot post Sem 6)
        sem6_milestones = [m for m in self.pkg.milestones if m.get("semester_target") == 6]
        self.assertEqual(len(sem6_milestones), 1)
        self.assertEqual(sem6_milestones[0]["title"], "Summer pilot (post Sem 6)")
        self.assertIn("8 weeks of pilot", sem6_milestones[0]["description"])

        # 3. Rules: S4, S5, S2
        # S4: Runway under 3 months with burn triggers freeze
        s4 = self.policy.s4_runway_guard(runway_months=2.0, monthly_burn=20000.0)
        self.assertTrue(s4["triggered"])
        self.assertTrue(s4["block_new_spend"])
        self.assertIn("SR08", s4["recommended_resources"])
        self.assertIn("SR09", s4["recommended_resources"])
        # Check Hard Rule 3: says "check the official page", no invented figures
        for lk in s4["resource_links"]:
            self.assertEqual(lk["note"], "check the official page")

        # S5: Public demo with unchecked IP
        s5 = self.policy.s5_ip_before_disclosure(public_demo_planned=True, ip_status="unchecked")
        self.assertTrue(s5["triggered"])
        self.assertEqual(s5["recommended_resource"], "SR07")
        self.assertTrue(s5["requires_institute_ip_policy_review"])

        # S2: Fallback check for MM student if CGPA drops to 6.3
        s2_mme = self.policy.s2_cgpa_guard(cgpa=6.3, semester=6, programme=student.programme_id)
        self.assertTrue(s2_mme["triggered"])
        self.assertEqual(s2_mme["fallback_goal"], "GOAL_FALLBACK_MME_CORE")
        self.assertTrue(s2_mme["fallback_is_stub"])

        # 4. Curriculum slot analysis (pre-NEP track from admission year 2024-25)
        slots = self.policy.get_curriculum_slots(student.programme_id, student.current_semester, admission_year="2024-25")
        self.assertEqual(slots["track"], "2016-17")
        self.assertEqual(slots["programme"], "BTECH_MM")

        # 5. Planning and Validation
        gaps = self.gap_analyzer.analyze_gaps(self.goal, self.reqs, skill_states)
        plan = self.planner.generate_plan(student, self.goal, gaps, [], [])
        report = self.validator.validate_plan(plan, student)
        self.assertTrue(report.passed, f"Validation failed: {report.messages}")
        self.assertGreater(len(plan.items), 0)

    def test_03_sem8_ee_student(self):
        """
        Scenario 3: Sem 8 EE student.
        - Traction decision milestone.
        - 5-item diagnostic assessment.
        - Rules: S6 placement interplay retrospective, S7 project alignment prompt only.
        - Plan generation & validation passed.
        """
        student = StudentProfile(
            student_id="STU_STARTUP_EE_SEM8",
            name="Rohan Verma",
            programme_id="BTECH_EE",
            current_semester=8,
            cgpa=8.0,
            backlogs=0,
            is_synthetic=True
        )

        # 1. 5-item Diagnostic Assessment from bank
        selected_items = self.diagnostic_items[10:15]
        self.assertEqual(len(selected_items), 5)
        ev_items = [
            EvidenceItem(
                evidence_id=f"EV_SEM8_{it['item_id']}",
                student_id=student.student_id,
                skill_id=it["skill_slug"],
                source_type="quiz",
                score=80.0 + (i * 3.0),
                recorded_at=datetime.now(timezone.utc)
            )
            for i, it in enumerate(selected_items)
        ]
        skill_states = self.state_updater.update_states(student.student_id, ev_items)

        # 2. Milestones verification (Sem 8: Traction decision)
        sem8_milestones = [m for m in self.pkg.milestones if m.get("semester_target") == 8]
        self.assertEqual(len(sem8_milestones), 1)
        self.assertEqual(sem8_milestones[0]["title"], "Traction decision")
        self.assertIn("continue / pause / job-first decision", sem8_milestones[0]["description"])

        # 3. Rules: S6 & S7
        # S6: Sem 7 placement registration preserved floor and mandated Sem 8 traction decision
        s6 = self.policy.s6_placement_interplay(semester=7, placement_registered=True)
        self.assertTrue(s6["triggered"])
        self.assertEqual(s6["floor_hours"], 5)
        self.assertEqual(s6["sem8_required_milestone"], "startup_traction_decision")

        # S7: Sem 8 project alignment displayed as PROMPT ONLY
        s7 = self.policy.s7_project_alignment(semester=8, project_topic_unrelated_to_venture=True)
        self.assertTrue(s7["triggered"])
        self.assertTrue(s7["prompt_only"])
        self.assertIn("aligning", s7["prompt"].lower())
        self.assertIn("venture prototype", s7["prompt"].lower())

        # 4. Curriculum slot analysis & project semester
        slots = self.policy.get_curriculum_slots(student.programme_id, student.current_semester, track="2016-17")
        self.assertIsNotNone(slots["project_alignment_prompt"])

        # 5. Planning and Validation
        gaps = self.gap_analyzer.analyze_gaps(self.goal, self.reqs, skill_states)
        plan = self.planner.generate_plan(student, self.goal, gaps, [], [])
        report = self.validator.validate_plan(plan, student)
        self.assertTrue(report.passed, f"Validation failed: {report.messages}")
        self.assertGreater(len(plan.items), 0)

    def test_04_unverified_resources_and_no_scheme_figures(self):
        """
        Test matching btech_upsc test_04:
        - SR12, SR14, and SR15 never appear as resource plan items for any of the 3 e2e students.
        - Any mention of them carries 'not confirmed yet'.
        - Skills without verified resources (SKILL_STARTUP_TECH_DEPTH and SKILL_STARTUP_TEAM_EXECUTION)
          have exercises with 'not confirmed yet'.
        - No plan item text contains a rupee amount (₹, Rs., INR, lakh, crore) or a deadline
          for Startup India, Startup Odisha, or IIT BBS REP.
        """
        # Load resources.csv to audit verification flags
        raw_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "higher_studies", "startup")
        )
        resources_map = {}
        with open(os.path.join(raw_dir, "resources.csv"), "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                resources_map[r["resource_id"]] = r

        unverified_rids = {"SR12", "SR14", "SR15"}
        for rid in unverified_rids:
            self.assertEqual(
                resources_map[rid]["verified"].strip().upper(),
                "FALSE",
                f"Resource {rid} expected verified=FALSE in raw data"
            )

        students = [
            StudentProfile(student_id="STU_E2E_EE_S3", name="Sem3 EE", programme_id="BTECH_EE", current_semester=3, cgpa=8.2, backlogs=0, is_synthetic=True),
            StudentProfile(student_id="STU_E2E_MM_S6", name="Sem6 MM", programme_id="BTECH_MM", current_semester=6, cgpa=7.5, backlogs=0, is_synthetic=True),
            StudentProfile(student_id="STU_E2E_EE_S8", name="Sem8 EE", programme_id="BTECH_EE", current_semester=8, cgpa=8.0, backlogs=0, is_synthetic=True)
        ]

        import re
        currency_pattern = re.compile(r"(\b(rs\.?|inr|rupees?|lakhs?|crores?)\b|₹)", re.IGNORECASE)
        scheme_keywords = ["startup india", "startup odisha", "rep", "research and entrepreneurship park", "entrepreneurship park"]
        deadline_keywords = ["deadline", "due date", "last date", "by 31st", "by 15th"]

        # Derive unverified skills from data: skills whose resources are ONLY verified=FALSE
        skill_verified_counts = {}
        for r in resources_map.values():
            sid = r.get("target_skill", "").strip()
            if not sid:
                continue
            is_v = (r.get("verified", "").strip().upper() == "TRUE")
            if sid not in skill_verified_counts:
                skill_verified_counts[sid] = {"verified": 0, "unverified": 0}
            if is_v:
                skill_verified_counts[sid]["verified"] += 1
            else:
                skill_verified_counts[sid]["unverified"] += 1

        unverified_skills = [
            sid for sid, counts in skill_verified_counts.items()
            if counts["verified"] == 0 and counts["unverified"] > 0
        ]

        for stu in students:
            gaps = self.gap_analyzer.analyze_gaps(self.goal, self.reqs, [])
            plan = self.planner.generate_plan(stu, self.goal, gaps, [], [])

            # 1. Check all resource items
            resource_items = [it for it in plan.items if it.item_type == "resource"]
            self.assertGreater(len(resource_items), 0, f"Plan for {stu.student_id} should include resources")

            assigned_rids = {it.resource_id for it in resource_items}
            for unv in unverified_rids:
                self.assertNotIn(
                    unv,
                    assigned_rids,
                    f"Unverified resource {unv} was assigned as a resource plan item for {stu.student_id}!"
                )

            for it in resource_items:
                rid = it.resource_id
                self.assertIn(rid, resources_map)
                self.assertEqual(
                    resources_map[rid]["verified"].strip().upper(),
                    "TRUE",
                    f"Resource {rid} in plan for {stu.student_id} must have verified=TRUE"
                )

            # 2. Check unverified skills exercises carry 'not confirmed yet'
            for sid in unverified_skills:
                matching_ex = [
                    it for it in plan.items
                    if it.item_type == "exercise" and sid in it.reason.target_skills
                ]
                self.assertGreater(len(matching_ex), 0, f"Missing exercise item for unverified skill {sid}")
                for ex in matching_ex:
                    self.assertIn(
                        "not confirmed yet",
                        ex.reason.why_this.lower(),
                        f"Exercise for unverified skill {sid} must contain 'not confirmed yet' for {stu.student_id}"
                    )

            # 3. Assert SR31 is assigned for SKILL_STARTUP_TEAM_EXECUTION
            team_exec_sr31 = [
                it for it in resource_items
                if "SKILL_STARTUP_TEAM_EXECUTION" in it.reason.target_skills and it.resource_id == "SR31"
            ]
            self.assertGreater(
                len(team_exec_sr31), 0,
                f"SKILL_STARTUP_TEAM_EXECUTION must have verified resource SR31 assigned for {stu.student_id}"
            )

            # 3. Check that ANY plan item mentioning unverified resources carries 'not confirmed yet'
            for it in plan.items:
                text = (
                    (it.reason.why_this or "") + " " +
                    " ".join(it.reason.rule_compliance or []) + " " +
                    (it.reason.intent or "")
                ).lower()

                if any(x in text for x in ["sr12", "sr14", "sr15", "hisrich", "nptel equivalents"]):
                    self.assertIn(
                        "not confirmed yet",
                        text,
                        f"Plan item {it.item_id} mentions unverified reference without 'not confirmed yet': {text}"
                    )

                # 4. Check no rupee amount or deadlines for schemes
                match_currency = currency_pattern.search(text)
                self.assertIsNone(
                    match_currency,
                    f"Plan item {it.item_id} contains forbidden currency token '{match_currency.group(0) if match_currency else ''}': {text}"
                )

                for dk in deadline_keywords:
                    if any(sk in text for sk in scheme_keywords):
                        self.assertNotIn(
                            dk,
                            text,
                            f"Plan item {it.item_id} contains deadline term '{dk}' for scheme: {text}"
                        )

if __name__ == "__main__":
    unittest.main()
