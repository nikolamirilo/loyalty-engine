"""Regression test for re-requesting a member login code (POST /auth/login).

What this guards:

  * Requesting again resends: a member who lost the first email gets a new one
    with a fresh code, and only that newest code signs them in.
  * Requesting again within RESEND_COOLDOWN answers 429 with Retry-After and
    sends nothing, rather than a 200 that pretends an email went out.
  * A code the member signed in with doesn't hold up the next request - logging
    in again right after (another device, after logging out) just works.
  * Signing in always lands in the default program, even when the request
    names another one.

Runs against an in-memory SQLite database with the Resend SDK stubbed out, so
it never touches Supabase and never sends mail.

Run: ./venv/bin/python -m tests.test_member_login_resend
"""

import os
import uuid
from datetime import timedelta

os.environ.setdefault("DATABASE_URL", "postgresql://u:p@h:6543/postgres")
os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("RESEND_API_KEY", "test-resend-key")
os.environ.setdefault("DOI_FROM_EMAIL", "noreply@example.com")

import resend
import sqlalchemy
from fastapi.testclient import TestClient
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
def _jsonb_on_sqlite(type_, compiler, **kw):  # postgres-only type
    return "JSON"


from app.main import app  # noqa: E402 - must be imported after the engine swap
from app.models import (  # noqa: E402
    Member,
    MemberIdentity,
    MemberLoginCode,
    Program,
)

# ...as must this, a postgres-only default SQLite cannot render.
Member.__table__.c.custom_attributes.server_default = None
database.Base.metadata.create_all(bind=database.engine)

PROGRAM_ID = uuid.uuid4()
OTHER_PROGRAM_ID = uuid.uuid4()
IDENTITY_ID = uuid.uuid4()
MEMBER_ID = uuid.uuid4()
EMAIL = "login@example.com"
HEADERS = {"Authorization": "Bearer test-token"}
client = TestClient(app, raise_server_exceptions=False)


def _login():
    return client.post("/auth/login", json={"email": EMAIL}, headers=HEADERS)


def _verify(code: str):
    return client.post(
        "/auth/verify",
        json={"email": EMAIL, "code": code},
        # Ignored: sign-in lands in the default program regardless.
        headers={**HEADERS, "X-Program-Id": "other"},
    )


def _sent_code(email) -> str:
    return email["text"].split("code is ")[1].split(".")[0]


def _age_codes(seconds: int) -> None:
    """Pretend every code was issued `seconds` earlier than it was."""
    session = database.SessionLocal()
    for row in session.query(MemberLoginCode).all():
        row.created_at = row.created_at - timedelta(seconds=seconds)
    session.commit()
    session.close()


def main() -> None:
    session = database.SessionLocal()
    session.add(Program(id=PROGRAM_ID, name="Test", slug="test", is_default=True))
    session.add(Program(id=OTHER_PROGRAM_ID, name="Other", slug="other"))
    session.add(MemberIdentity(id=IDENTITY_ID, name="Login Member", email=EMAIL))
    # Already enrolled everywhere, so login has no memberships to create.
    session.add(Member(id=MEMBER_ID, program_id=PROGRAM_ID, identity_id=IDENTITY_ID))
    session.add(Member(program_id=OTHER_PROGRAM_ID, identity_id=IDENTITY_ID))
    session.commit()
    session.close()

    failures = []
    original_send = resend.Emails.send
    sent = []

    def recording_send(params, *_args, **_kwargs):
        sent.append(params)
        return {"id": f"email_{len(sent)}"}

    try:
        resend.Emails.send = recording_send

        first = _login()
        if first.status_code != 200:
            failures.append(f"first login answered {first.status_code}, expected 200")
        if len(sent) != 1:
            failures.append(f"first login sent {len(sent)} emails, expected 1")

        # Straight away again: refused with 429, nothing sent.
        hurried = _login()
        if hurried.status_code != 429:
            failures.append(f"re-request within cooldown answered {hurried.status_code}, expected 429")
        if not hurried.headers.get("Retry-After", "").isdigit():
            failures.append(f"429 carried Retry-After {hurried.headers.get('Retry-After')!r}")
        if len(sent) != 1:
            failures.append(f"re-request within cooldown sent an email ({len(sent)} total)")

        # Past the cooldown: a new email, and only its code signs in.
        _age_codes(61)
        resent = _login()
        if resent.status_code != 200 or len(sent) != 2:
            failures.append(
                f"re-request after cooldown answered {resent.status_code} with "
                f"{len(sent)} emails sent in total, expected 200 and 2"
            )
        old_code, new_code = _sent_code(sent[0]), _sent_code(sent[-1])
        if old_code != new_code and _verify(old_code).status_code != 400:
            failures.append("the superseded login code still signed in")
        signed_in = _verify(new_code)
        if signed_in.status_code != 200:
            failures.append(f"newest login code answered {signed_in.status_code} {signed_in.text}")
        elif signed_in.json()["member"]["programId"] != str(PROGRAM_ID):
            failures.append(
                f"signed in to program {signed_in.json()['member']['programId']}, "
                f"expected the default {PROGRAM_ID}"
            )

        # Signing in again right away isn't a resend, so no cooldown applies.
        again = _login()
        if again.status_code != 200 or len(sent) != 3:
            failures.append(
                f"login right after signing in answered {again.status_code} with "
                f"{len(sent)} emails sent in total, expected 200 and 3"
            )
    finally:
        resend.Emails.send = original_send

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("OK: /auth/login resends a fresh code, rate-limits with 429, and lands in the default program")


if __name__ == "__main__":
    main()
