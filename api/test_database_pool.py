"""Regression test for the Supabase connection-pool configuration.

Guards against re-introducing a persistent client-side connection pool, which
in the serverless (Vercel) deployment caused every function instance to hold
its own set of open connections. Under load those piled up against the Supabase
pooler until it rejected new connections with:

    FATAL: (EMAXCONNSESSION) max clients reached in session mode

The engine must use SQLAlchemy's NullPool so each request opens exactly one
connection and closes it, never leaking connections between invocations.

Run: ./venv/bin/python test_database_pool.py
"""

import os

# database.py requires these at import time; set harmless placeholders.
os.environ.setdefault("DATABASE_URL", "postgresql://u:p@h:6543/postgres")
os.environ.setdefault("API_TOKEN", "test-token")

from sqlalchemy.pool import NullPool

from database import engine


def main() -> None:
    failures = []

    if not isinstance(engine.pool, NullPool):
        failures.append(
            f"engine must use NullPool for serverless, got {type(engine.pool).__name__}"
        )

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("OK: engine uses NullPool (no persistent connections held per instance)")


if __name__ == "__main__":
    main()
