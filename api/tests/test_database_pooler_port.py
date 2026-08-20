"""Regression test for the Supabase pooler port used by DATABASE_URL.

Production was configured with the *session* pooler (port 5432), whose client
budget is a handful of connections. Under serverless load every request that
couldn't get one died with:

    FATAL: (EMAXCONNSESSION) max clients reached in session mode
           - max clients are limited to pool_size: 15

`_prefer_transaction_pooler` redirects such a URL to the transaction pooler
(port 6543), the mode built for many short-lived connections.

Run: ./venv/bin/python -m tests.test_database_pooler_port
"""

import os

# app.core.config requires these at import time; set harmless placeholders.
os.environ.setdefault("DATABASE_URL", "postgresql://u:p@h:6543/postgres")
os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("RESEND_API_KEY", "test-resend-key")
os.environ.setdefault("DOI_FROM_EMAIL", "noreply@example.com")

from app.core.database import _prefer_transaction_pooler

SESSION = "postgresql://postgres.abc:pw@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"
TRANSACTION = "postgresql://postgres.abc:pw@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"

CASES = {
    # The misconfiguration that caused the outage.
    SESSION: TRANSACTION,
    # Query strings and other options must survive the rewrite.
    f"{SESSION}?sslmode=require": f"{TRANSACTION}?sslmode=require",
    # Already transaction mode -> untouched.
    TRANSACTION: TRANSACTION,
    # Not a Supabase pooler: 5432 is the normal Postgres port, leave it alone.
    "postgresql://u:p@db.example.com:5432/postgres": (
        "postgresql://u:p@db.example.com:5432/postgres"
    ),
    # Direct (non-pooled) Supabase host on 5432 is also left alone.
    "postgresql://postgres:pw@db.abc.supabase.co:5432/postgres": (
        "postgresql://postgres:pw@db.abc.supabase.co:5432/postgres"
    ),
}


def main() -> None:
    failures = []

    for raw, expected in CASES.items():
        got = _prefer_transaction_pooler(raw)
        if got != expected:
            failures.append(f"({raw!r}) = {got!r}, expected {expected!r}")

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print(f"OK: {len(CASES)} DATABASE_URL cases resolve to the right pooler port")


if __name__ == "__main__":
    main()
