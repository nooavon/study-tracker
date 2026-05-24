#!/bin/sh
set -e

# 1. Wait for the database to be ready
echo "Waiting for database..."
python3 - <<'PY'
import os
import time
import psycopg

database_url = os.environ["DATABASE_URL"]
for _ in range(60):
    try:
        with psycopg.connect(database_url):
            break
    except psycopg.OperationalError:
        time.sleep(1)
else:
    raise SystemExit("Database did not become available in time.")
PY

# 2. Run migrations
echo "Running migrations..."
python3 -m app.migrate

# 3. Start the application
echo "Starting Uvicorn..."
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
