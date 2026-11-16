"""Waits for PostgreSQL. Exit 0 = seeded, 10 = reachable but empty (seed it), 1 = not reachable."""
import os
import sys
import time

import psycopg

url = os.environ.get("DATABASE_URL", "").replace("+psycopg", "")
for i in range(60):
    try:
        with psycopg.connect(url, connect_timeout=3) as conn, conn.cursor() as cur:
            cur.execute("SELECT to_regclass('kb.course') IS NOT NULL AND to_regclass('student.student') IS NOT NULL")
            if not cur.fetchone()[0]:
                print("Schema not present yet: seeding.")
                sys.exit(10)
            cur.execute("SELECT (SELECT COUNT(*) FROM kb.course), (SELECT COUNT(*) FROM student.student)")
            courses, students = cur.fetchone()
            print(f"Database connected: {courses} courses, {students} students.")
            sys.exit(10 if (courses == 0 or students == 0) else 0)
    except Exception as e:  # database still starting
        print(f"Waiting for database ({i + 1}/60): {str(e).splitlines()[0][:100]}")
        time.sleep(1)
print("Database wait timed out.")
sys.exit(1)
