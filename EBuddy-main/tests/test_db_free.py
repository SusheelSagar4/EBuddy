import os
import re
import csv
import json
import unittest
import app.config  # Loads Pydantic settings & LiteLLM flags

class TestDBFree(unittest.TestCase):
    """
    DB-Free Unit Tests: Can run in any environment without database or Docker services.
    Covers configuration, environment variables, SQL schema definitions, and seed data integrity.
    """

    def test_01_env_example_compliance(self):
        """Verify Hard Rule 2 & 3: .env.example exists and lists all required variables."""
        self.assertTrue(os.path.exists(".env.example"), ".env.example must exist")
        with open(".env.example", encoding="utf-8") as f:
            content = f.read()

        required_vars = [
            "LLM_MODEL=",
            "LLM_API_KEY=",
            "LLM_API_BASE=",
            "EMBEDDING_MODEL=",
            "LITELLM_LOCAL_MODEL_COST_MAP=True",
            "LITELLM_TELEMETRY=False"
        ]
        for var in required_vars:
            self.assertIn(var, content, f"Variable {var} missing in .env.example")

    def test_02_env_git_and_docker_ignored(self):
        """Verify Hard Rule 5: .env is git-ignored and docker-ignored; .env.example is not."""
        self.assertTrue(os.path.exists(".gitignore"), ".gitignore missing")
        self.assertTrue(os.path.exists(".dockerignore"), ".dockerignore missing")

        with open(".gitignore", encoding="utf-8") as f:
            gi = f.read()
            self.assertIn(".env", gi)
            self.assertIn("!.env.example", gi)

        with open(".dockerignore", encoding="utf-8") as f:
            di = f.read()
            self.assertIn(".env", di)
            self.assertIn("!.env.example", di)

    def test_03_no_hardcoded_secrets_or_endpoints(self):
        """Verify Hard Rule 2: Scan code to ensure no hardcoded API keys or model endpoints exist."""
        secret_patterns = [
            r"sk-[a-zA-Z0-9]{20,}",
            r"AIza[0-9A-Za-z-_]{35}",
            r"https://api\.openai\.com/v1"
        ]
        target_dirs = ["app", "scripts"]
        for td in target_dirs:
            for root, _, files in os.walk(td):
                for fn in files:
                    if fn.endswith(".py"):
                        fpath = os.path.join(root, fn)
                        with open(fpath, encoding="utf-8") as f:
                            text = f.read()
                        for pat in secret_patterns:
                            matches = re.findall(pat, text)
                            self.assertEqual(len(matches), 0, f"Found hardcoded pattern {pat} in {fpath}")

    def test_04_docker_compose_platforms(self):
        """Verify Hard Rule 4: docker-compose defines app, db, adminer with platform: linux/amd64."""
        self.assertTrue(os.path.exists("docker-compose.yml"), "docker-compose.yml missing")
        with open("docker-compose.yml", encoding="utf-8") as f:
            compose_text = f.read()

        self.assertIn("services:", compose_text)
        self.assertIn("db:", compose_text)
        self.assertIn("adminer:", compose_text)
        self.assertIn("app:", compose_text)
        
        # Check platform: linux/amd64 occurrences (must be present for all 3 services)
        platforms = re.findall(r"platform:\s*linux/amd64", compose_text)
        self.assertGreaterEqual(len(platforms), 3, "linux/amd64 platform must be specified for all 3 services")

    def test_05_litellm_airgap_flags(self):
        """Verify Hard Rule 8: LiteLLM local cost map is True and telemetry is False."""
        self.assertEqual(os.environ.get("LITELLM_LOCAL_MODEL_COST_MAP"), "True")
        self.assertEqual(os.environ.get("LITELLM_TELEMETRY"), "False")

    def test_06_sql_schema_syntax_and_schemas(self):
        """Verify Section 4: docker/init.sql defines kb, student, plan, ops schemas with foreign keys."""
        init_sql_path = os.path.join("docker", "init.sql")
        self.assertTrue(os.path.exists(init_sql_path), "docker/init.sql missing")
        with open(init_sql_path, encoding="utf-8") as f:
            sql = f.read()

        schemas = ["kb", "student", "plan", "ops"]
        for s in schemas:
            self.assertIn(f"CREATE SCHEMA IF NOT EXISTS {s};", sql, f"Schema {s} creation statement missing")

        # Check required key tables
        expected_tables = [
            "kb.source", "kb.course", "kb.course_prerequisite", "kb.programme_requirement",
            "kb.slot_option", "kb.skill", "kb.resource", "kb.exercise", "kb.goal",
            "kb.research_project", "kb.faculty", "kb.data_issue",
            "student.student", "student.completed_course", "student.skill_evidence",
            "student.skill_state", "student.goal", "student.constraint",
            "plan.plan", "plan.plan_item", "plan.validation_report", "plan.plan_diff",
            "ops.reprocess_queue", "ops.llm_call_log"
        ]
        for tbl in expected_tables:
            self.assertIn(tbl, sql, f"Table {tbl} definition missing in docker/init.sql")

        # Verify source_id exists on kb.course, kb.resource, kb.exercise, kb.research_project
        self.assertIn("source_id VARCHAR(100) REFERENCES kb.source", sql)

    def test_07_seed_data_presence(self):
        """Verify Hard Rule 6: Seed data exists in data/seed/kb/."""
        seed_kb = os.path.join("data", "seed", "kb")
        expected_files = [
            "source.csv", "department.csv", "programme.csv", "course.csv",
            "course_alias.csv", "course_prerequisite.csv", "course_offering.csv",
            "programme_requirement.csv", "slot_option.csv", "academic_rule.json",
            "skill.csv", "resource.csv", "resource_course.csv", "research_area.csv",
            "faculty.csv", "research_project.csv", "consultancy_engagement.csv",
            "publication.csv", "project_faculty.csv",
            "project_keyword.csv", "data_issue.csv", "mastery_criteria.json"
        ]
        for fn in expected_files:
            fpath = os.path.join(seed_kb, fn)
            self.assertTrue(os.path.exists(fpath), f"Seed file missing: {fpath}")

    def test_08_addendum1_parsed_counts(self):
        """Verify exact parsed entity counts across EE and MME programmes."""
        seed_kb = os.path.join("data", "seed", "kb")

        with open(os.path.join(seed_kb, "course.csv"), encoding="utf-8") as f:
            courses = [r for r in csv.reader(f) if r]
        self.assertEqual(len(courses) - 1, 136, "Expected exactly 136 courses across EE and MME")

        with open(os.path.join(seed_kb, "programme_requirement.csv"), encoding="utf-8") as f:
            reqs = list(csv.DictReader(f))
        slots = [r for r in reqs if not r.get("course_id")]
        self.assertEqual(len(slots), 25, "Expected exactly 25 programme slots (13 EE + 12 MME)")
        self.assertEqual(len(reqs), 141, "Expected 141 total programme requirements (25 slots + course requirements per programme)")

        with open(os.path.join(seed_kb, "research_project.csv"), encoding="utf-8") as f:
            projects = [r for r in csv.reader(f) if r]
        self.assertEqual(len(projects) - 1, 196, "Expected exactly 196 research projects (138 EE + 58 MME after removing 17 consultancy entries)")

        with open(os.path.join(seed_kb, "faculty.csv"), encoding="utf-8") as f:
            fac = list(csv.DictReader(f))
        persons = [x for x in fac if x["is_person"].lower() == "true"]
        groups = [x for x in fac if x["is_person"].lower() == "false"]
        self.assertEqual(len(persons), 44, "Expected exactly 44 persons (28 EE + 16 MME)")
        self.assertEqual(len(groups), 7, "Expected exactly 7 groups")

    def test_09_faculty_name_isolation(self):
        """Verify no person contains '&', 'Team', or 'Group'."""
        seed_kb = os.path.join("data", "seed", "kb")
        with open(os.path.join(seed_kb, "faculty.csv"), encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if r["is_person"].lower() == "true":
                    name = r["display_name"]
                    self.assertNotIn("&", name)
                    self.assertNotIn("Team", name)
                    self.assertNotIn("Group", name)

if __name__ == "__main__":
    unittest.main()

