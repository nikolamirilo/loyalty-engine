"""Standalone regression test for DATABASE_URL scheme normalization.

Reproduces the Vercel FUNCTION_INVOCATION_FAILED crash: when the connection
string uses a bare `postgresql://` (or `+psycopg2`) scheme, SQLAlchemy defaults
to the psycopg2 driver, which is no longer installed -> ModuleNotFoundError.

Run: ./venv/bin/python test_database_url.py
"""

import os

# database.py requires these at import time; set harmless placeholders.
os.environ.setdefault("DATABASE_URL", "postgresql://u:p@h:6543/postgres")
os.environ.setdefault("API_TOKEN", "test-token")

from sqlalchemy import create_engine

from database import _normalize_database_url

CASES = {
    # Supabase hands out this bare scheme by default.
    "postgresql://u:p@h:6543/postgres": "postgresql+psycopg://u:p@h:6543/postgres",
    # Old explicit psycopg2 driver.
    "postgresql+psycopg2://u:p@h:6543/postgres": "postgresql+psycopg://u:p@h:6543/postgres",
    # Heroku-style short scheme.
    "postgres://u:p@h:6543/postgres": "postgresql+psycopg://u:p@h:6543/postgres",
    # Already correct -> left untouched.
    "postgresql+psycopg://u:p@h:6543/postgres": "postgresql+psycopg://u:p@h:6543/postgres",
}


def main() -> None:
    failures = []

    for raw, expected in CASES.items():
        got = _normalize_database_url(raw)
        if got != expected:
            failures.append(f"normalize({raw!r}) = {got!r}, expected {expected!r}")
            continue
        # The whole point: creating the engine must not try to import psycopg2.
        try:
            engine = create_engine(got)
            assert engine.dialect.driver == "psycopg", engine.dialect.driver
        except ModuleNotFoundError as exc:
            failures.append(f"{raw!r} still triggers driver import error: {exc}")

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print(f"OK: {len(CASES)} cases normalized to the psycopg (v3) driver")


if __name__ == "__main__":
    main()
