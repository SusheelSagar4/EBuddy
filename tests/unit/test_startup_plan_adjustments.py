import os
import csv
import re
import unittest
from typing import Set
from app.contracts.student import StudentProfile
from app.contracts.goal import Goal, GoalRequirement
from app.personas.registry import persona_registry
from app.engine.planner import Planner
from app.engine.gaps import GapAnalyzer

class TestStartupPlanAdjustments(unittest.TestCase):
    """
    Unit tests for Startup plan item adjustments (mirroring btech_upsc test_plan_adjustments):
    - Check 4 passes for Sem 3 EE student.
    - Check 4 passes for Sem 6 MM student.
    - ee_power_core plan output is unchanged.
    - No verified=FALSE resource (SR12, SR14, SR15) is ever assigned as a plan item.
    - Unverified resources carry 'not confirmed yet'.
    - No rupee amounts or deadlines for schemes are present.
    - Deterministic item generation.
    """
    @classmethod
    def setUpClass(cls):
        persona_registry.discover()
        cls.startup_pkg = persona_registry.get("student_startup")
        cls.ee_pkg = persona_registry.get("ee_power_core")
        cls.planner = Planner()
        cls.gap_analyzer = GapAnalyzer()

        # Load resources.csv to audit verification status
        raw_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "higher_studies", "startup")
        )
        cls.resources_map = {}
        with open(os.path.join(raw_dir, "resources.csv"), "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                cls.resources_map[r["resource_id"]] = r

    def _get_startup_goal_and_reqs(self):
        goal = Goal(
            goal_id=self.startup_pkg.spec.goal_id,
            name="Student Startup Founder",
            category="startup",
            description=self.startup_pkg.spec.description,
            source_id="DESIGN_TEAM"
        )
        reqs = [
            GoalRequirement(
                goal_id=goal.goal_id,
                skill_id=r["skill_id"],
                required_level=float(r["required_level"]),
                importance=float(r.get("importance", 1.0)),
                source_id="DESIGN_TEAM"
            )
            for r in self.startup_pkg.requirements
        ]
        return goal, reqs

    def test_01_check_4_passes_sem3_ee(self):
        """Check 4 passes for Sem 3 EE student (all 10 startup skills covered)."""
        student = StudentProfile(
            student_id="STU_EE_SEM3_STARTUP",
            name="Aarav Startup",
            programme_id="BTECH_EE",
            current_semester=3,
            cgpa=8.2,
            backlogs=0,
            is_synthetic=True
        )
        goal, reqs = self._get_startup_goal_and_reqs()
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
        plan = self.planner.generate_plan(student, goal, gaps, [], [])

        covered_skills: Set[str] = set()
        for it in plan.items:
            covered_skills.update(it.reason.target_skills)

        for g in gaps:
            if g["gap"] > 0:
                self.assertIn(
                    g["skill_id"],
                    covered_skills,
                    f"Skill {g['skill_id']} not covered in plan for Sem 3 EE"
                )

    def test_02_check_4_passes_sem6_mm(self):
        """Check 4 passes for Sem 6 MM student (all 10 startup skills covered)."""
        student = StudentProfile(
            student_id="STU_MM_SEM6_STARTUP",
            name="Ananya Startup MM",
            programme_id="BTECH_MM",
            current_semester=6,
            cgpa=7.4,
            backlogs=0,
            is_synthetic=True
        )
        goal, reqs = self._get_startup_goal_and_reqs()
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
        plan = self.planner.generate_plan(student, goal, gaps, [], [])

        covered_skills: Set[str] = set()
        for it in plan.items:
            covered_skills.update(it.reason.target_skills)

        for g in gaps:
            if g["gap"] > 0:
                self.assertIn(
                    g["skill_id"],
                    covered_skills,
                    f"Skill {g['skill_id']} not covered in plan for Sem 6 MM"
                )

    def test_03_ee_power_core_plan_unchanged(self):
        """Ensure ee_power_core plan output remains completely untouched and valid."""
        student = StudentProfile(
            student_id="STU_EE_CORE_CHK",
            name="EE Core Student",
            programme_id="BTECH_EE",
            current_semester=5,
            cgpa=7.8,
            is_synthetic=True
        )
        goal = Goal(
            goal_id=self.ee_pkg.spec.goal_id,
            name="EE Power Core",
            category="career",
            description="Power Core",
            source_id="TEST"
        )
        reqs = [
            GoalRequirement(
                goal_id=goal.goal_id,
                skill_id=r["skill_id"],
                required_level=float(r["required_level"]),
                source_id="TEST"
            )
            for r in self.ee_pkg.requirements
        ]
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
        plan = self.planner.generate_plan(student, goal, gaps, [], [])

        expected_structure = [
            ('course', 'EE3L004', ['SKILL_POWER_ELECTRONICS']),
            ('exercise', 'EE3L004', ['SKILL_POWER_ELECTRONICS']),
            ('course', 'EE3L007', ['SKILL_POWER_SYSTEMS']),
            ('exercise', 'EE3L007', ['SKILL_POWER_SYSTEMS']),
            ('course', 'EE3L010', []),
            ('exercise', 'EE3L010', []),
            ('course', 'EE3L011', []),
            ('exercise', 'EE3L011', []),
            ('course', 'EE3P004', ['SKILL_POWER_ELECTRONICS']),
            ('exercise', 'EE3P004', ['SKILL_POWER_ELECTRONICS']),
            ('course', 'EE3P005', ['SKILL_INSTRUMENTATION']),
            ('exercise', 'EE3P005', ['SKILL_INSTRUMENTATION']),
            ('course', 'EE3L005', ['SKILL_CONTROL_SYSTEMS']),
            ('exercise', 'EE3L005', ['SKILL_CONTROL_SYSTEMS']),
            ('course', 'EE3L006', []),
            ('exercise', 'EE3L006', []),
            ('course', 'EC6L012', []),
            ('exercise', 'EC6L012', []),
            ('milestone', None, ['SKILL_ELECTRIC_MACHINES', 'SKILL_POWER_SYSTEMS', 'SKILL_CIRCUIT_ANALYSIS', 'SKILL_POWER_ELECTRONICS', 'SKILL_RENEWABLE_ENERGY'])
        ]
        actual_structure = [(it.item_type, it.course_id, it.reason.target_skills) for it in plan.items]
        self.assertEqual(actual_structure, expected_structure)

    def test_04_no_unverified_resource_and_no_scheme_amounts(self):
        """
        Hard Rule 2 & 3:
        - SR12, SR14, SR15 never appear as resource plan items.
        - Any mention carries 'not confirmed yet'.
        - No plan item text contains rupee amounts or scheme deadlines.
        """
        unverified_rids = {"SR12", "SR14", "SR15"}
        for rid in unverified_rids:
            self.assertEqual(self.resources_map[rid]["verified"].strip().upper(), "FALSE")

        currency_pattern = re.compile(r"(\b(rs\.?|inr|rupees?|lakhs?|crores?)\b|₹)", re.IGNORECASE)
        scheme_keywords = ["startup india", "startup odisha", "rep", "research and entrepreneurship park"]
        deadline_keywords = ["deadline", "due date", "last date", "by 31st", "by 15th"]

        # Derive unverified-skill list from data: skills whose resources are ONLY verified=FALSE
        skill_verified_counts = {}
        for r in self.resources_map.values():
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

        for prog in ["BTECH_EE", "BTECH_MM"]:
            student = StudentProfile(
                student_id=f"STU_VER_CHK_{prog}",
                name="Verification Student",
                programme_id=prog,
                current_semester=5,
                is_synthetic=True
            )
            goal, reqs = self._get_startup_goal_and_reqs()
            gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])
            plan = self.planner.generate_plan(student, goal, gaps, [], [])

            resource_items = [it for it in plan.items if it.item_type == "resource"]
            self.assertGreater(len(resource_items), 0)

            # Assert SR12, SR14, SR15 never appear as resource plan items
            assigned_rids = {it.resource_id for it in resource_items}
            for unv in unverified_rids:
                self.assertNotIn(unv, assigned_rids)

            for it in resource_items:
                rid = it.resource_id
                self.assertEqual(self.resources_map[rid]["verified"].strip().upper(), "TRUE")

            # Check exercise items for unverified skills (derived from data)
            for sid in unverified_skills:
                ex_items = [it for it in plan.items if it.item_type == "exercise" and sid in it.reason.target_skills]
                self.assertGreater(len(ex_items), 0, f"Missing exercise item for unverified skill {sid}")
                for ex in ex_items:
                    self.assertIn("not confirmed yet", ex.reason.why_this.lower())

            # Assert SR31 is assigned for SKILL_STARTUP_TEAM_EXECUTION
            team_exec_items = [
                it for it in resource_items
                if "SKILL_STARTUP_TEAM_EXECUTION" in it.reason.target_skills and it.resource_id == "SR31"
            ]
            self.assertGreater(
                len(team_exec_items), 0,
                "SKILL_STARTUP_TEAM_EXECUTION must have verified resource SR31 assigned as a plan item"
            )

            # Check text across all items
            for it in plan.items:
                text = (
                    (it.reason.why_this or "") + " " +
                    " ".join(it.reason.rule_compliance or []) + " " +
                    (it.reason.intent or "")
                ).lower()

                if any(x in text for x in ["sr12", "sr14", "sr15", "hisrich", "nptel equivalents"]):
                    self.assertIn("not confirmed yet", text)

                # No rupee amounts
                match_currency = currency_pattern.search(text)
                self.assertIsNone(match_currency, f"Found currency token in {text}")

                # No scheme deadlines
                for dk in deadline_keywords:
                    if any(sk in text for sk in scheme_keywords):
                        self.assertNotIn(dk, text)

    def test_05_deterministic_plan_items(self):
        """Pick resources and exercises deterministically so same inputs give identical plan."""
        student = StudentProfile(
            student_id="STU_DETERMINISTIC",
            name="Deterministic Student",
            programme_id="BTECH_EE",
            current_semester=4,
            is_synthetic=True
        )
        goal, reqs = self._get_startup_goal_and_reqs()
        gaps = self.gap_analyzer.analyze_gaps(goal, reqs, [])

        plan1 = self.planner.generate_plan(student, goal, gaps, [], [])
        plan2 = self.planner.generate_plan(student, goal, gaps, [], [])

        items1 = [(it.item_type, it.resource_id, it.exercise_id, it.reason.target_skills) for it in plan1.items]
        items2 = [(it.item_type, it.resource_id, it.exercise_id, it.reason.target_skills) for it in plan2.items]
        self.assertEqual(items1, items2)

if __name__ == "__main__":
    unittest.main()
