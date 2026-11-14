"""
Database Seed Loader & System Reset Engine.
Loads plain CSV/JSON files from data/seed/ in topological foreign-key order.
Idempotent, fails loudly on schema/FK mismatch, and logs row counts per table.
"""

import os
import sys
import csv
import json
import argparse
from typing import Dict, Any, List
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ebuddy_user:ebuddy_password@127.0.0.1:5432/ebuddy")
LOCAL_DATABASE_URL = os.getenv("LOCAL_DATABASE_URL", "postgresql://ebuddy_user:ebuddy_password@127.0.0.1:5432/ebuddy")

# If running locally on host outside docker, resolve @db: to @127.0.0.1:
if "@db:" in DATABASE_URL and not os.path.exists("/.dockerenv"):
    DATABASE_URL = LOCAL_DATABASE_URL

if DATABASE_URL.startswith("postgresql+psycopg://"):
    PG_CONN_STRING = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
else:
    PG_CONN_STRING = DATABASE_URL

def get_connection():
    try:
        conn = psycopg.connect(PG_CONN_STRING, connect_timeout=3)
        return conn
    except Exception as e:
        print(f"[ERROR] Could not connect to database at {PG_CONN_STRING} (timeout=3s): {e}")
        return None

def reset_database(conn):
    print("Dropping existing schemas (kb, student, plan, ops)...")
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS plan CASCADE;")
        cur.execute("DROP SCHEMA IF EXISTS student CASCADE;")
        cur.execute("DROP SCHEMA IF EXISTS kb CASCADE;")
        cur.execute("DROP SCHEMA IF EXISTS ops CASCADE;")
        conn.commit()

    print("Re-executing docker/init.sql...")
    init_sql_path = os.path.join(os.path.dirname(__file__), "..", "docker", "init.sql")
    with open(init_sql_path, encoding="utf-8") as f:
        init_sql = f.read()

    with conn.cursor() as cur:
        cur.execute(init_sql)
        conn.commit()
    print("Schemas and tables successfully recreated.")

def load_csv(conn, file_path: str, table_name: str) -> int:
    if not os.path.exists(file_path):
        return 0

    with open(file_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return 0

        rows = list(reader)
        if not rows:
            return 0

        placeholders = ", ".join(["%s"] * len(headers))
        cols = ", ".join(headers)
        query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;"

        with conn.cursor() as cur:
            # Clean empty strings to None for nullable columns
            cleaned_rows = []
            for r in rows:
                cleaned_rows.append([None if val == "" else val for val in r])
            cur.executemany(query, cleaned_rows)
            conn.commit()
            return len(rows)

def load_json(conn, file_path: str, table_name: str, cols: List[str]) -> int:
    if not os.path.exists(file_path):
        return 0

    with open(file_path, encoding="utf-8") as f:
        items = json.load(f)

    if not items:
        return 0

    placeholders = ", ".join(["%s"] * len(cols))
    col_str = ", ".join(cols)
    query = f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;"

    rows = []
    for item in items:
        row = []
        for col in cols:
            val = item.get(col)
            if isinstance(val, (dict, list)):
                row.append(json.dumps(val))
            else:
                row.append(val)
        rows.append(row)

    with conn.cursor() as cur:
        cur.executemany(query, rows)
        conn.commit()
    return len(rows)

def load_all_seeds(conn):
    print("Loading seed files from data/seed/ in topological FK order...")
    seed_kb = os.path.join(os.path.dirname(__file__), "..", "data", "seed", "kb")
    seed_student = os.path.join(os.path.dirname(__file__), "..", "data", "seed", "student")

    table_load_order = [
        # KB base
        (load_csv, os.path.join(seed_kb, "source.csv"), "kb.source"),
        (load_csv, os.path.join(seed_kb, "department.csv"), "kb.department"),
        (load_csv, os.path.join(seed_kb, "programme.csv"), "kb.programme"),
        (load_csv, os.path.join(seed_kb, "course.csv"), "kb.course"),
        (load_csv, os.path.join(seed_kb, "course_alias.csv"), "kb.course_alias"),
        (load_csv, os.path.join(seed_kb, "course_prerequisite.csv"), "kb.course_prerequisite"),
        (load_csv, os.path.join(seed_kb, "course_offering.csv"), "kb.course_offering"),
        (load_csv, os.path.join(seed_kb, "programme_requirement.csv"), "kb.programme_requirement"),
        (load_csv, os.path.join(seed_kb, "slot_option.csv"), "kb.slot_option"),
        (load_csv, os.path.join(seed_kb, "minor.csv"), "kb.minor"),
        (load_csv, os.path.join(seed_kb, "minor_course.csv"), "kb.minor_course"),
        (lambda c, p, t: load_json(c, p, t, ["rule_id", "rule_type", "parameters", "human_text", "status", "source_id"]),
         os.path.join(seed_kb, "academic_rule.json"), "kb.academic_rule"),
        (load_csv, os.path.join(seed_kb, "skill.csv"), "kb.skill"),
        (load_csv, os.path.join(seed_kb, "skill_prerequisite.csv"), "kb.skill_prerequisite"),
        (load_csv, os.path.join(seed_kb, "course_skill.csv"), "kb.course_skill"),
        (load_csv, os.path.join(seed_kb, "module.csv"), "kb.module"),
        (load_csv, os.path.join(seed_kb, "module_skill.csv"), "kb.module_skill"),
        (load_csv, os.path.join(seed_kb, "resource.csv"), "kb.resource"),
        (load_csv, os.path.join(seed_kb, "resource_skill.csv"), "kb.resource_skill"),
        (load_csv, os.path.join(seed_kb, "resource_course.csv"), "kb.resource_course"),
        (load_csv, os.path.join(seed_kb, "exercise.csv"), "kb.exercise"),
        (load_csv, os.path.join(seed_kb, "goal.csv"), "kb.goal"),
        (load_csv, os.path.join(seed_kb, "goal_skill_requirement.csv"), "kb.goal_skill_requirement"),
        (load_csv, os.path.join(seed_kb, "goal_milestone.csv"), "kb.goal_milestone"),
        (lambda c, p, t: load_json(c, p, t, ["criteria_id", "goal_id", "skill_id", "criteria", "status", "source_id"]),
         os.path.join(seed_kb, "mastery_criteria.json"), "kb.mastery_criteria"),
        (load_csv, os.path.join(seed_kb, "research_area.csv"), "kb.research_area"),
        (load_csv, os.path.join(seed_kb, "faculty.csv"), "kb.faculty"),
        (load_csv, os.path.join(seed_kb, "research_project.csv"), "kb.research_project"),
        (load_csv, os.path.join(seed_kb, "consultancy_engagement.csv"), "kb.consultancy_engagement"),
        (load_csv, os.path.join(seed_kb, "publication.csv"), "kb.publication"),
        (load_csv, os.path.join(seed_kb, "project_faculty.csv"), "kb.project_faculty"),
        (load_csv, os.path.join(seed_kb, "project_keyword.csv"), "kb.project_keyword"),
        (load_csv, os.path.join(seed_kb, "keyword_skill.csv"), "kb.keyword_skill"),
        (load_csv, os.path.join(seed_kb, "data_issue.csv"), "kb.data_issue"),

        # Core to Core feature tables (Section 5 & 6)
        (load_csv, os.path.join(os.path.dirname(__file__), "..", "data", "seed", "core_to_core", "academic_calendar.csv"), "kb.academic_calendar"),
        (load_csv, os.path.join(os.path.dirname(__file__), "..", "data", "seed", "core_to_core", "area_skills.csv"), "kb.area_skill"),
        (load_csv, os.path.join(os.path.dirname(__file__), "..", "data", "seed", "core_to_core", "faculty_areas.csv"), "kb.faculty_area"),
        (load_csv, os.path.join(os.path.dirname(__file__), "..", "data", "seed", "core_to_core", "papers.csv"), "kb.paper"),
        (load_csv, os.path.join(os.path.dirname(__file__), "..", "data", "seed", "core_to_core", "paper_authors.csv"), "kb.paper_author"),
        (load_csv, os.path.join(os.path.dirname(__file__), "..", "data", "seed", "core_to_core", "paper_chunks.csv"), "kb.paper_chunk"),
        (load_csv, os.path.join(os.path.dirname(__file__), "..", "data", "seed", "core_to_core", "paper_skills.csv"), "kb.paper_skill"),
        (load_csv, os.path.join(os.path.dirname(__file__), "..", "data", "seed", "core_to_core", "taster_tasks.csv"), "kb.taster_task"),
        (load_csv, os.path.join(os.path.dirname(__file__), "..", "data", "seed", "core_to_core", "industry_milestones.csv"), "kb.industry_milestone"),

        # Student data
        (load_csv, os.path.join(seed_student, "student.csv"), "student.student"),
        (load_csv, os.path.join(seed_student, "completed_course.csv"), "student.completed_course"),
        (load_csv, os.path.join(seed_student, "student_goal.csv"), "student.goal"),
        (load_csv, os.path.join(seed_student, "interest.csv"), "student.interest"),
        (load_csv, os.path.join(seed_student, "skill_evidence.csv"), "student.skill_evidence"),
        (load_csv, os.path.join(seed_student, "skill_state.csv"), "student.skill_state"),
        (load_csv, os.path.join(seed_student, "constraint.csv"), "student.constraint"),
        (load_csv, os.path.join(seed_student, "preference.csv"), "student.preference")
    ]

    total_loaded = 0
    print("\n--- Seed Insertion Summary ---")
    for loader_func, fpath, tname in table_load_order:
        if os.path.exists(fpath):
            count = loader_func(conn, fpath, tname)
            print(f"  {tname:35s}: {count:5d} rows loaded from {os.path.basename(fpath)}")
            total_loaded += count
        else:
            # Table seed file does not exist yet (e.g. Phase 3 student seeds)
            pass

    # Clear ops.reprocess_queue so initial seed insertions don't leave spurious pending events
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE ops.reprocess_queue;")
        conn.commit()
    print("  ops.reprocess_queue: Truncated to 0 (clean state after initial seed load)")

    print(f"\nTotal rows loaded: {total_loaded}")
    
    print("\n--- Verified PostgreSQL Database Row Counts ---")
    verified_tables = [
        "kb.source", "kb.department", "kb.programme", "kb.course",
        "kb.course_alias", "kb.course_prerequisite", "kb.course_offering",
        "kb.programme_requirement", "kb.slot_option", "kb.minor",
        "kb.minor_course", "kb.academic_rule", "kb.skill",
        "kb.resource", "kb.resource_course", "kb.goal",
        "kb.mastery_criteria", "kb.research_area", "kb.faculty",
        "kb.research_project", "kb.consultancy_engagement", "kb.publication",
        "kb.project_faculty", "kb.project_keyword", "kb.data_issue",
        "kb.academic_calendar", "kb.area_skill", "kb.faculty_area",
        "kb.paper", "kb.paper_author", "kb.paper_chunk", "kb.paper_skill",
        "kb.taster_task", "kb.industry_milestone"
    ]
    with conn.cursor() as cur:
        for t in verified_tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t};")
                cnt = cur.fetchone()[0]
                print(f"  {t:35s}: {cnt:5d} rows in DB")
            except Exception as e:
                print(f"  {t:35s}: Error checking count: {e}")
    return total_loaded

def main():
    parser = argparse.ArgumentParser(description="Load seed CSV/JSON files into PostgreSQL database.")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate schemas before loading seeds.")
    args = parser.parse_args()

    conn = get_connection()
    if not conn:
        print("[FAIL] Database unavailable. Exiting.")
        sys.exit(1)

    try:
        if args.reset:
            reset_database(conn)
        load_all_seeds(conn)
        print("Database operation complete.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
