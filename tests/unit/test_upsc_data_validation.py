import os
import csv
import yaml
import unittest

class TestUPSCDataValidation(unittest.TestCase):
    """
    Task 1 Data Validation Tests.
    Verifies that all UPSC domain datasets, CSV schemas, referential integrity,
    template phase totals, diagnostic item banks, and fact rows strictly comply
    with EBuddy rules.
    """
    @classmethod
    def setUpClass(cls):
        cls.raw_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "higher_studies", "upsc")
        cls.inst_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "institute")
        cls.seed_kb = os.path.join(os.path.dirname(__file__), "..", "..", "data", "seed", "kb")

    def test_01_csv_column_counts(self):
        """Verify that no CSV has bad/mismatched column counts or ragged rows."""
        self.assertTrue(os.path.exists(self.raw_dir), f"Directory {self.raw_dir} does not exist")
        csv_files = [(self.raw_dir, f) for f in os.listdir(self.raw_dir) if f.endswith(".csv")]
        if os.path.exists(self.inst_dir):
            csv_files.extend([(self.inst_dir, f) for f in os.listdir(self.inst_dir) if f.endswith(".csv")])
        self.assertTrue(len(csv_files) >= 9, f"Expected at least 9 CSVs, found {len(csv_files)}")

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

    def test_02_template_phases_sum_to_100(self):
        """Verify that every UPSC preparation template's phase shares total exactly 100%."""
        # Check raw prep_template_phases_upsc.csv
        phases_fp = os.path.join(self.raw_dir, "prep_template_phases_upsc.csv")
        self.assertTrue(os.path.exists(phases_fp), "prep_template_phases_upsc.csv missing")
        shares_by_template = {}
        with open(phases_fp, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                tid = r["template_id"]
                pct = float(r["share_pct"])
                shares_by_template[tid] = shares_by_template.get(tid, 0.0) + pct

        for tid in ["UPSC-24", "UPSC-12", "UPSC-6"]:
            self.assertIn(tid, shares_by_template, f"Template {tid} missing from phases")
            self.assertAlmostEqual(
                shares_by_template[tid], 100.0, places=2,
                msg=f"Template {tid} phases do not total 100: got {shares_by_template[tid]}"
            )

        # Check integrated template_phases.csv in data/raw/higher_studies/
        integrated_fp = os.path.join(self.raw_dir, "..", "template_phases.csv")
        if os.path.exists(integrated_fp):
            int_shares = {}
            with open(integrated_fp, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    tid = r["template_id"]
                    if tid.startswith("UPSC-"):
                        int_shares[tid] = int_shares.get(tid, 0.0) + float(r["share_of_weeks"])
            for tid in ["UPSC-24", "UPSC-12", "UPSC-6"]:
                self.assertIn(tid, int_shares, f"Template {tid} missing from integrated phases")
                self.assertAlmostEqual(int_shares[tid], 1.0, places=2)

    def test_03_referential_integrity(self):
        """Verify all referenced skill, milestone, and resource IDs exist without dangling references."""
        # Load valid skills from skills.csv
        skills_fp = os.path.join(self.raw_dir, "skills.csv")
        valid_skills = set()
        with open(skills_fp, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                valid_skills.add(r["skill_slug"].strip())
        self.assertEqual(len(valid_skills), 12, "Expected 12 unique UPSC skills")

        # Load valid milestones from milestones.csv
        milestones_fp = os.path.join(self.raw_dir, "milestones.csv")
        valid_milestones = set()
        with open(milestones_fp, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                ms = r["milestone_slug"].strip()
                valid_milestones.add(ms)
                # Check skills referenced in milestone
                req_skills = [s.strip() for s in r["required_skills"].split(";") if s.strip()]
                for s in req_skills:
                    if s == "GS_ALL":
                        continue
                    self.assertIn(s, valid_skills, f"Milestone {ms} references non-existent skill {s}")

        # Check diagnostic blueprint skills
        diag_yaml_fp = os.path.join(self.raw_dir, "diagnostic.yaml")
        with open(diag_yaml_fp, "r", encoding="utf-8") as f:
            diag_meta = yaml.safe_load(f)
            target_skills = diag_meta["blueprint"]["target_skills"]
            for s in target_skills:
                self.assertIn(s, valid_skills, f"diagnostic.yaml references non-existent skill {s}")

        # Check diagnostic items skill references
        items_fp = os.path.join(self.raw_dir, "diagnostic_items.csv")
        with open(items_fp, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                sid = r["skill_slug"].strip()
                self.assertIn(sid, valid_skills, f"Item {r['item_id']} references non-existent skill {sid}")

        # Check resources referential integrity
        res_fp = os.path.join(self.raw_dir, "resources.csv")
        with open(res_fp, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                ts = r["target_skill"].strip()
                ms = r["milestone"].strip()
                if ts:
                    self.assertIn(ts, valid_skills, f"Resource {r['resource_id']} references unknown skill {ts}")
                if ms:
                    self.assertIn(ms, valid_milestones, f"Resource {r['resource_id']} references unknown milestone {ms}")

    def test_04_diagnostic_items_bank(self):
        """Verify 15 items per target skill, 45 total items, and difficulty within [30.0, 70.0]."""
        items_fp = os.path.join(self.raw_dir, "diagnostic_items.csv")
        diag_yaml_fp = os.path.join(self.raw_dir, "diagnostic.yaml")
        with open(diag_yaml_fp, "r", encoding="utf-8") as f:
            diag_meta = yaml.safe_load(f)
            target_skills = diag_meta["blueprint"]["target_skills"]

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

    def test_05_fact_rows_integrity(self):
        """Verify all fact rows have non-empty source_url, retrieved_on, applies_to_cycle, and verified."""
        facts_fp = os.path.join(self.raw_dir, "facts.csv")
        self.assertTrue(os.path.exists(facts_fp), "facts.csv is missing")
        with open(facts_fp, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertGreaterEqual(len(rows), 20, "Expected at least 20 fact rows")
            for r in rows:
                fid = r["fact_id"]
                url = r["source_url"].strip()
                retrieved = r["retrieved_on"].strip()
                cycle = (r.get("applies_to_cycle") or r.get("cycle") or "").strip()
                verified = r["verified"].strip().upper()

                val = r.get("value", "").strip()
                if val == "NOT_FOUND" and verified == "FALSE":
                    # source_url may be empty only when value is NOT_FOUND and verified=FALSE
                    pass
                else:
                    self.assertTrue(bool(url), f"Fact {fid} is missing source_url")
                self.assertTrue(bool(retrieved), f"Fact {fid} is missing retrieved_on")
                self.assertTrue(bool(cycle), f"Fact {fid} is missing applies_to_cycle")
                self.assertIn(verified, ["TRUE", "FALSE"], f"Fact {fid} verified flag must be TRUE or FALSE, got '{verified}'")

if __name__ == "__main__":
    unittest.main()
