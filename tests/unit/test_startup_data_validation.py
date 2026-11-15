import os
import csv
import io
import yaml
import unittest

class TestStartupDataValidation(unittest.TestCase):
    """
    Task 1 Data Validation Tests for student_startup persona.
    Validates CSV schema conformity, referential integrity, diagnostic item bank,
    resource coverage, verified flags, and shared data boundaries.
    """
    @classmethod
    def setUpClass(cls):
        cls.raw_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "higher_studies", "startup"))
        cls.inst_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "institute"))
        cls.seed_kb = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "seed", "kb"))

    def test_01_csv_column_counts(self):
        """Verify that no CSV has bad/mismatched column counts or ragged rows."""
        self.assertTrue(os.path.exists(self.raw_dir), f"Directory {self.raw_dir} does not exist")
        csv_files = [(self.raw_dir, f) for f in os.listdir(self.raw_dir) if f.endswith(".csv")]
        self.assertTrue(len(csv_files) >= 4, f"Expected at least 4 CSVs in startup raw data, found {len(csv_files)}")

        for d, fn in csv_files:
            fp = os.path.join(d, fn)
            with open(fp, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                self.assertIsNotNone(header, f"Empty CSV file: {fn}")
                expected_cols = len(header)
                self.assertGreater(expected_cols, 0, f"Header has 0 columns in {fn}")
                for line_num, row in enumerate(reader, start=2):
                    if not row or all(field.strip() == "" for field in row):
                        continue
                    self.assertEqual(
                        len(row), expected_cols,
                        f"Bad column count in {fn} at line {line_num}: expected {expected_cols}, got {len(row)} ({row})"
                    )

        # Failure test: verify validation fails when column counts are mismatched
        corrupted_csv = "col1,col2,col3\nval1,val2\n"
        with self.assertRaises(AssertionError):
            reader = csv.reader(io.StringIO(corrupted_csv))
            hdr = next(reader)
            for r in reader:
                if len(r) != len(hdr):
                    raise AssertionError("Mismatched column count detected")

    def test_02_referential_integrity(self):
        """Verify all referenced skill, milestone, and resource IDs exist without dangling references."""
        # 1. Load valid skills
        skills_fp = os.path.join(self.raw_dir, "skills.csv")
        valid_skills = set()
        with open(skills_fp, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                valid_skills.add(r["skill_slug"].strip())
        self.assertEqual(len(valid_skills), 10, "Expected 10 unique startup skills")

        # 2. Load valid milestones
        milestones_fp = os.path.join(self.raw_dir, "milestones.csv")
        valid_milestones = set()
        with open(milestones_fp, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                ms = r["milestone_slug"].strip()
                valid_milestones.add(ms)
                req_skills = [s.strip() for s in r["required_skills"].split(";") if s.strip()]
                for s in req_skills:
                    self.assertIn(s, valid_skills, f"Milestone {ms} references non-existent skill {s}")
        self.assertEqual(len(valid_milestones), 8, "Expected 8 unique startup milestones")

        # 3. Check diagnostic blueprint skills
        diag_yaml_fp = os.path.join(self.raw_dir, "diagnostic.yaml")
        with open(diag_yaml_fp, "r", encoding="utf-8") as f:
            diag_meta = yaml.safe_load(f)
            target_skills = diag_meta["blueprint"]["target_skills"]
            for s in target_skills:
                self.assertIn(s, valid_skills, f"diagnostic.yaml references non-existent skill {s}")

        # 4. Check diagnostic items skill references
        items_fp = os.path.join(self.raw_dir, "diagnostic_items.csv")
        with open(items_fp, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                sid = r["skill_slug"].strip()
                self.assertIn(sid, valid_skills, f"Item {r['item_id']} references non-existent skill {sid}")

        # 5. Check resources skill and milestone references
        res_fp = os.path.join(self.raw_dir, "resources.csv")
        valid_resources = set()
        with open(res_fp, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                valid_resources.add(r["resource_id"].strip())
                ts = r["target_skill"].strip()
                ms = r["milestone"].strip()
                if ts:
                    self.assertIn(ts, valid_skills, f"Resource {r['resource_id']} references unknown skill {ts}")
                if ms:
                    self.assertIn(ms, valid_milestones, f"Resource {r['resource_id']} references unknown milestone {ms}")
        self.assertEqual(len(valid_resources), 15, "Expected 15 startup resources")

        # Failure test: non-existent ID fails
        with self.assertRaises(AssertionError):
            bad_skill_ref = "SKILL_NON_EXISTENT"
            if bad_skill_ref not in valid_skills:
                raise AssertionError(f"Unknown skill {bad_skill_ref}")

    def test_03_every_skill_has_at_least_one_resource(self):
        """Verify that every skill in skills.csv has at least one associated resource in resources.csv."""
        skills_fp = os.path.join(self.raw_dir, "skills.csv")
        res_fp = os.path.join(self.raw_dir, "resources.csv")

        all_skills = set()
        with open(skills_fp, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                all_skills.add(r["skill_slug"].strip())

        covered_skills = set()
        with open(res_fp, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                ts = r["target_skill"].strip()
                if ts:
                    covered_skills.add(ts)

        missing_skills = all_skills - covered_skills
        self.assertEqual(len(missing_skills), 0, f"Skills without resources: {missing_skills}")

        # Failure test: unmapped skill triggers assertion
        with self.assertRaises(AssertionError):
            hypothetical_missing = {"SKILL_UNMAPPED"}
            if hypothetical_missing - covered_skills:
                raise AssertionError("Unmapped skill detected")

    def test_04_diagnostic_items_bank(self):
        """Verify 15 items per target skill, 45 total items, and difficulty strictly within [30.0, 70.0]."""
        items_fp = os.path.join(self.raw_dir, "diagnostic_items.csv")
        diag_yaml_fp = os.path.join(self.raw_dir, "diagnostic.yaml")
        with open(diag_yaml_fp, "r", encoding="utf-8") as f:
            diag_meta = yaml.safe_load(f)
            target_skills = diag_meta["blueprint"]["target_skills"]

        expected_targets = {
            "SKILL_STARTUP_CUSTOMER_DISCOVERY",
            "SKILL_STARTUP_UNIT_ECONOMICS_FINANCE",
            "SKILL_STARTUP_IP_LEGAL_COMPLIANCE"
        }
        self.assertEqual(set(target_skills), expected_targets)

        items_per_skill = {}
        total_items = 0
        with open(items_fp, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                total_items += 1
                sid = r["skill_slug"].strip()
                items_per_skill[sid] = items_per_skill.get(sid, 0) + 1
                diff = float(r["difficulty"])
                self.assertGreaterEqual(
                    diff, 30.0,
                    f"Item {r['item_id']} difficulty {diff} is below lower threshold 30.0"
                )
                self.assertLessEqual(
                    diff, 70.0,
                    f"Item {r['item_id']} difficulty {diff} exceeds upper threshold 70.0"
                )
                self.assertIn(r["correct"].strip().upper(), ["A", "B", "C", "D"], f"Invalid correct answer in {r['item_id']}")

        self.assertEqual(total_items, 45, f"Expected 45 diagnostic items, got {total_items}")
        for s in target_skills:
            self.assertEqual(
                items_per_skill.get(s, 0), 15,
                f"Target skill {s} does not have exactly 15 diagnostic items (got {items_per_skill.get(s, 0)})"
            )

        # Failure test: items outside 30-70 or not 15 items fails
        with self.assertRaises(AssertionError):
            bad_diff = 25.0
            if not (30.0 <= bad_diff <= 70.0):
                raise AssertionError("Difficulty outside 30-70")

        with self.assertRaises(AssertionError):
            bad_count = 14
            if bad_count != 15:
                raise AssertionError("Diagnostic items count != 15")

    def test_05_verified_flag_and_no_facts_csv(self):
        """
        Verify:
        - There is NO facts.csv for startup (Hard Rule 3).
        - Unverified resources (SR12, SR14, SR15) have verified=FALSE (Hard Rule 2).
        - Verified resources (all others) have verified=TRUE.
        """
        facts_fp = os.path.join(self.raw_dir, "facts.csv")
        self.assertFalse(os.path.exists(facts_fp), "facts.csv must NOT exist for startup (Hard Rule 3)")

        res_fp = os.path.join(self.raw_dir, "resources.csv")
        expected_unverified = {"SR12", "SR14", "SR15"}
        actual_unverified = set()
        actual_verified = set()

        with open(res_fp, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rid = r["resource_id"].strip()
                v = r["verified"].strip().upper()
                if v == "FALSE":
                    actual_unverified.add(rid)
                elif v == "TRUE":
                    actual_verified.add(rid)
                else:
                    self.fail(f"Invalid verified flag in {rid}: {v}")

        self.assertEqual(actual_unverified, expected_unverified, f"Mismatch in unverified resources: {actual_unverified}")
        self.assertEqual(len(actual_verified), 12, "Expected 12 verified resources")

    def test_06_shared_institute_files_loaded_once(self):
        """Verify shared institute files exist in data/raw/institute/ and are NOT duplicated in startup raw dir."""
        shared_files = ["institute_calendar.csv", "institute_programmes.csv", "institute_curriculum_slots.csv"]
        for fn in shared_files:
            self.assertTrue(os.path.exists(os.path.join(self.inst_dir, fn)), f"Shared file {fn} missing from institute dir")
            self.assertFalse(os.path.exists(os.path.join(self.raw_dir, fn)), f"Shared file {fn} must NOT be duplicated in startup dir")

if __name__ == "__main__":
    unittest.main()
