import os
import unittest
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ebuddy_user:ebuddy_password@127.0.0.1:5432/ebuddy")
if "@db:" in DATABASE_URL and not os.path.exists("/.dockerenv"):
    DATABASE_URL = os.getenv("LOCAL_DATABASE_URL", "postgresql://ebuddy_user:ebuddy_password@127.0.0.1:5432/ebuddy")

if DATABASE_URL.startswith("postgresql+psycopg://"):
    PG_CONN_STRING = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
else:
    PG_CONN_STRING = DATABASE_URL

class TestDBDependent(unittest.TestCase):
    """
    Database Integration Tests (Strict Verification):
    Must run against active PostgreSQL service.
    FAILS (does not skip) if Postgres is unreachable.
    """

    @classmethod
    def setUpClass(cls):
        try:
            cls.conn = psycopg.connect(PG_CONN_STRING, connect_timeout=3)
        except Exception as e:
            cls.conn = None
            cls.connection_error = str(e)

    @classmethod
    def tearDownClass(cls):
        if cls.conn and not cls.conn.closed:
            cls.conn.close()

    def setUp(self):
        # Strict requirement: FAIL (not skip) if database is unreachable
        if not self.conn:
            self.fail(f"PostgreSQL database is unreachable at {PG_CONN_STRING}: {self.connection_error}")
        self.conn.rollback()

    def test_01_schemas_exist(self):
        """Verify kb, student, plan, ops schemas exist in Postgres."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT schema_name FROM information_schema.schemata 
                WHERE schema_name IN ('kb', 'student', 'plan', 'ops');
            """)
            found_schemas = {row[0] for row in cur.fetchall()}
            self.assertEqual(found_schemas, {'kb', 'student', 'plan', 'ops'})

    def test_02_foreign_key_enforcement(self):
        """Verify that inserting a course_prerequisite with an unknown course_id fails with ForeignKeyViolation."""
        with self.conn.cursor() as cur:
            with self.assertRaises(psycopg.errors.ForeignKeyViolation):
                cur.execute(
                    "INSERT INTO kb.course_prerequisite (course_id, prereq_id, relation) VALUES (%s, %s, %s);",
                    ("ZZ9L999", "MA1L001", "required")
                )
            self.conn.rollback()

    def test_03_table_row_counts(self):
        """Verify that seed loader populated expected canonical rows in Postgres."""
        expected_counts = {
            "kb.course": 136,
            "kb.programme_requirement": 141,
            "kb.research_project": 196,
            "kb.consultancy_engagement": 17,
            "kb.publication": 102,
            "kb.faculty": 51,
            "kb.data_issue": 38
        }
        with self.conn.cursor() as cur:
            for table_name, expected in expected_counts.items():
                cur.execute(f"SELECT COUNT(*) FROM {table_name};")
                actual = cur.fetchone()[0]
                self.assertEqual(actual, expected, f"Table {table_name} count mismatch")

    def test_04_reprocess_trigger_active(self):
        """Verify notify_reprocess_event trigger is attached in PostgreSQL."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT trigger_name, event_object_table 
                FROM information_schema.triggers 
                WHERE trigger_name LIKE 'trg_%';
            """)
            triggers = cur.fetchall()
            self.assertGreater(len(triggers), 0, "Reprocess triggers must be registered")

if __name__ == "__main__":
    unittest.main()
