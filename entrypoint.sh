#!/bin/sh
set -e

# Wait for PostgreSQL to become available before running migrations
python - <<'PY'
import os
import time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

db_url = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/postgres",
)

engine = create_engine(db_url)
print("Waiting for database...", flush=True)
while True:
    try:
        with engine.connect():
            break
    except OperationalError:
        time.sleep(1)

print("Database is ready", flush=True)
PY

# Run database migrations
alembic upgrade head

exec "$@"
