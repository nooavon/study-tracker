#!/bin/sh
set -eu

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

python3 -m app.migrate

exec python3 -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-dir /app/app \
  --reload-dir /app/migrations