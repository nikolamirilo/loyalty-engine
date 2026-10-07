"""Regression test for what POST /doi/trigger does when called twice.

What this guards:

  * Triggering again resends: a member who lost the first email gets a new one
    with a fresh code, and only that newest code verifies.
  * Triggering again within RESEND_COOLDOWN answers 429 with Retry-After and
    sends nothing, rather than a 200 that pretends an email went out.
  * A failed send must leave no code row behind - that row is what starts the
    cooldown, and starting it for a code that was never delivered would block
    the member's retry for nothing.

Runs against an in-memory SQLite database with the Resend SDK stubbed out, so
it never touches Supabase and never sends mail.

Run: ./venv/bin/python -m tests.regression.test_doi_trigger_flow
"""

import os
import uuid
from datetime import timedelta

os.environ.setdefault("DATABASE_URL", "postgresql://u:p@h:6543/postgres")
os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("RESEND_API_KEY", "test-resend-key")
os.environ.setdefault("EMAIL_FROM", "noreply@example.com")

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
from app.models import (  # noqa: E402
    EmailVerificationCode,
    Member,
    MemberIdentity,
    Program,
)

# ...as must this, a postgres-only default SQLite cannot render.
Member.__table__.c.custom_attributes.server_default = None
database.Base.metadata.create_all(
    bind=database.engine,
    tables=[
        Program.__table__,
        MemberIdentity.__table__,
        Member.__table__,
        EmailVerificationCode.__table__,
    ],
)

PROGRAM_ID = uuid.uuid4()
IDENTITY_ID = uuid.uuid4()
MEMBER_ID = uuid.uuid4()
HEADERS = {"Authorization": "Bearer test-token"}
client = TestClient(app, raise_server_exceptions=False)


def _trigger():
    return client.post(
        "/doi/trigger", json={"memberId": str(MEMBER_ID)}, headers=HEADERS
    )


def _sent_code(email) -> str:
    return email["text"].split("code is ")[1].split(".")[0]


def _verify(code: str):
    return client.post(
        "/doi/verify",
        json={"memberId": str(MEMBER_ID), "code": code},
        headers=HEADERS,
    )


def _age_codes(seconds: int) -> None:
    """Pretend every code was issued `seconds` earlier than it was."""
    session = database.SessionLocal()
    for row in session.query(EmailVerificationCode).all():
        row.created_at = row.created_at - timedelta(seconds=seconds)
    session.commit()
    session.close()


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
    # No X-Program-Id header is sent below, so the request resolves to the
    # default program - which is why this one is flagged as such.
    session.add(Program(id=PROGRAM_ID, name="Test", slug="test", is_default=True))
    session.add(
        MemberIdentity(id=IDENTITY_ID, name="Test Member", email="member@example.com")
    )
    session.add(Member(id=MEMBER_ID, program_id=PROGRAM_ID, identity_id=IDENTITY_ID))
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
        status = _trigger().status_code
        if status != 500:
            failures.append(f"permanent send failure answered {status}, expected 500")
        if _active_codes():
            failures.append("a failed send left a code row behind")

        def recording_send(params, *_args, **_kwargs):
            sent.append(params)
            return {"id": f"email_{len(sent)}"}

        resend.Emails.send = recording_send

        # The failed send above started no cooldown, so this goes straight out.
        first = _trigger()
        if first.status_code != 200:
            failures.append(f"first trigger answered {first.status_code}, expected 200")
        if len(sent) != 1:
            failures.append(f"first trigger sent {len(sent)} emails, expected 1")

        # Straight away again: refused with 429, nothing sent, first code intact.
        hurried = _trigger()
        if hurried.status_code != 429:
            failures.append(f"re-trigger within cooldown answered {hurried.status_code}, expected 429")
        retry_after = hurried.headers.get("Retry-After", "")
        if not retry_after.isdigit() or not 0 < int(retry_after) <= 60:
            failures.append(f"429 carried Retry-After {retry_after!r}, expected 1-60")
        if len(sent) != 1:
            failures.append(f"re-trigger within cooldown sent an email ({len(sent)} total)")

        # Once the cooldown has passed, the member gets a new email and code.
        _age_codes(61)
        resent = _trigger()
        if resent.status_code != 200:
            failures.append(f"re-trigger after cooldown answered {resent.status_code}, expected 200")
        if len(sent) != 2:
            failures.append(f"re-trigger after cooldown sent {len(sent)} emails in total, expected 2")
        if len(_active_codes()) != 1:
            failures.append(f"expected 1 outstanding code, found {len(_active_codes())}")

        # The first email's code was retired; only the newest one verifies.
        old_code, new_code = _sent_code(sent[0]), _sent_code(sent[-1])
        if old_code != new_code:
            stale = _verify(old_code)
            if stale.status_code != 400:
                failures.append(f"superseded code answered {stale.status_code}, expected 400")
        response = _verify(new_code)
        if response.status_code != 200 or not response.json().get("verified"):
            failures.append(
                f"verifying the newest emailed code answered {response.status_code} "
                f"{response.text}"
            )
    finally:
        resend.Emails.send = original_send

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("OK: /doi/trigger resends a fresh code, rate-limits with 429, and persists nothing on failure")


if __name__ == "__main__":
    main()
