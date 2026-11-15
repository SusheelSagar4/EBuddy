#!/bin/sh
set -e

echo "=== EBuddy Web Application Initializing ==="

python -c "
import os, sys, time, psycopg

db_url = os.environ.get('DATABASE_URL', 'postgresql://ebuddy_user:ebuddy_password@db:5432/ebuddy')
if '+psycopg' in db_url:
    db_url = db_url.replace('+psycopg', '')

print('Checking PostgreSQL database connection...')
for i in range(30):
    try:
        conn = psycopg.connect(db_url, connect_timeout=3)
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM kb.course;')
            cnt = cur.fetchone()[0]
            print(f'Database connected. Existing courses count: {cnt}')
            if cnt == 0:
                print('Database empty! Triggering seed load...')
                sys.exit(10)
            else:
                print('Database already seeded.')
                sys.exit(0)
    except Exception as e:
        print(f'Waiting for database (attempt {i+1}/30)...')
        time.sleep(1)

print('Database wait timed out.')
sys.exit(1)
" || STATUS=$?

if [ "$STATUS" = "10" ]; then
    echo "Running database seed loader..."
    python scripts/seed_loader.py --reset
fi

echo "Starting Uvicorn HTTP server on 0.0.0.0:8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
