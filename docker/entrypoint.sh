#!/bin/sh
# Entry point of the app container.
#   (default)   wait for PostgreSQL, seed it if empty, start the web server
#   reset       restore the database to the original seed state and exit
set -e
cd /app

if [ "$1" = "reset" ]; then
    echo "=== Restoring the database to the original seed state ==="
    exec python scripts/seed_loader.py --reset
fi

echo "=== EBuddy starting ==="
STATUS=0
python docker/wait_for_db.py || STATUS=$?
if [ "$STATUS" = "10" ]; then
    echo "Seeding database..."
    python scripts/seed_loader.py --reset
elif [ "$STATUS" != "0" ]; then
    echo "WARNING: database not reachable; starting in seed-file mode (plans are computed in memory)."
fi

echo "Starting web server on 0.0.0.0:8000 (web app at /app/)"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
