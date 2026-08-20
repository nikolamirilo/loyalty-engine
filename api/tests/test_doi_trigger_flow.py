"""Regression test for what POST /doi/trigger does when called twice.

Two behaviours this guards:

  * While the member's code is still live, triggering again must answer exactly
    as the first call did and send nothing. A second email would invalidate the
    first, so a member reading the older one would type a dead code.
  * A failed send must leave no code row behind - that row is what suppresses
    the next trigger, and suppressing it for a code that was never delivered
    locks the member out for the full code lifetime.

Runs against an in-memory SQLite database with the Resend SDK stubbed out, so
it never touches Supabase and never sends mail.

Run: ./venv/bin/python -m tests.test_doi_trigger_flow
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

os.environ.setdefault("DATABASE_URL", "postgresql://u:p@h:6543/postgres")
os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("RESEND_API_KEY", "test-resend-key")
os.environ.setdefault("DOI_FROM_EMAIL", "noreply@example.com")

import resend
import sqlalchemy
from fastapi.testclient import TestClient
from resend.exceptions import ResendError
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

import app.core.database as database

# One shared in-memory connection: SQLite drops the database when the last
# connection closes, and the app's NullPool closes one after every request.
database.engine = sqlalchemy.create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
database.SessionLocal.configure(bind=database.engine)


@compiles(JSONB, "sqlite")
def _jsonb_on_sqlite(type_, compiler, **kw):  # postgres-only type, unused by DOI
    return "JSON"


from app.main import app  # noqa: E402 - must be imported after the engine swap
from app.models import EmailVerificationCode, Member  # noqa: E402

# ...as must this, a postgres-only default SQLite cannot render.
Member.__table__.c.custom_attributes.server_default = None
database.Base.metadata.create_all(
    bind=database.engine, tables=[Member.__table__, EmailVerificationCode.__table__]
)

MEMBER_ID = uuid.uuid4()
HEADERS = {"Authorization": "Bearer test-token"}
client = TestClient(app, raise_server_exceptions=False)


def _trigger():
    response = client.post(
        "/doi/trigger", json={"memberId": str(MEMBER_ID)}, headers=HEADERS
    )
    return response.status_code, response.text


def _active_codes():
    session = database.SessionLocal()
    try:
        return (
            session.query(EmailVerificationCode)
            .filter(EmailVerificationCode.consumed_at.is_(None))
            .all()
        )
    finally:
        session.close()


def main() -> None:
    session = database.SessionLocal()
    session.add(Member(id=MEMBER_ID, name="Test Member", email="member@example.com"))
    session.commit()
    session.close()

    failures = []
    original_send = resend.Emails.send
    sent = []

    try:
        # A rejected send must not persist anything.
        def rejecting_send(*_args, **_kwargs):
            raise ResendError(
                code=403,
                error_type="validation_error",
                message="The example.com domain is not verified.",
                suggested_action="Verify the domain.",
            )

        resend.Emails.send = rejecting_send
        status, _ = _trigger()
        if status != 500:
            failures.append(f"permanent send failure answered {status}, expected 500")
        if _active_codes():
            failures.append("a failed send left a code row behind")

        def recording_send(params, *_args, **_kwargs):
            sent.append(params)
            return {"id": f"email_{len(sent)}"}

        resend.Emails.send = recording_send

        first = _trigger()
        if first[0] != 200:
            failures.append(f"first trigger answered {first[0]}, expected 200")
        if len(sent) != 1:
            failures.append(f"first trigger sent {len(sent)} emails, expected 1")

        # Re-triggering while that code is live: same answer, no second email.
        again = _trigger()
        if again != first:
            failures.append(
                f"re-trigger answered {again}, expected the first response {first}"
            )
        if len(sent) != 1:
            failures.append(f"re-trigger sent another email ({len(sent)} total)")
        if len(_active_codes()) != 1:
            failures.append(f"expected 1 outstanding code, found {len(_active_codes())}")

        # Once it expires, the next trigger issues a fresh code.
        session = database.SessionLocal()
        row = (
            session.query(EmailVerificationCode)
            .filter(EmailVerificationCode.consumed_at.is_(None))
            .one()
        )
        row.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
            seconds=1
        )
        session.commit()
        session.close()

        expired = _trigger()
        if expired[0] != 200:
            failures.append(f"trigger after expiry answered {expired[0]}, expected 200")
        if len(sent) != 2:
            failures.append(
                f"trigger after expiry sent {len(sent)} emails in total, expected 2"
            )

        # The newest emailed code is the one that verifies.
        code = sent[-1]["text"].split("code is ")[1].split(".")[0]
        response = client.post(
            "/doi/verify",
            json={"memberId": str(MEMBER_ID), "code": code},
            headers=HEADERS,
        )
        if response.status_code != 200 or not response.json().get("verified"):
            failures.append(
                f"verifying the emailed code answered {response.status_code} "
                f"{response.text}"
            )
    finally:
        resend.Emails.send = original_send

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("OK: /doi/trigger is idempotent while a code is live, and persists nothing on failure")


if __name__ == "__main__":
    main()
