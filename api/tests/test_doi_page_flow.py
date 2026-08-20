"""Regression test for POST /doi/trigger with `type: "page"`.

What this guards:

  * `type: "page"` mails a link to the client's /verify page carrying the
    member id and the raw code - that link *is* the flow, so a missing or
    malformed one breaks verification for every member who gets it.
  * The code inside that link is the one /doi/verify accepts.
  * Type is part of what "already satisfied" means: re-triggering the same type
    while the code is live still sends nothing, but asking for the other type
    issues a fresh code. Only the hash is stored, so the emailed link can never
    be rebuilt - leaving the code alone there would answer 200 while the member
    never receives the link they were promised.
  * `type: "page"` without CLIENT_BASE_URL configured fails loudly (500) and
    persists nothing, rather than mailing a broken button.

Runs against an in-memory SQLite database with the Resend SDK stubbed out, so
it never touches Supabase and never sends mail.

Run: ./venv/bin/python -m tests.test_doi_page_flow
"""

import os
import uuid
from html import unescape
from urllib.parse import parse_qs, urlparse

os.environ.setdefault("DATABASE_URL", "postgresql://u:p@h:6543/postgres")
os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("RESEND_API_KEY", "test-resend-key")
os.environ.setdefault("DOI_FROM_EMAIL", "noreply@example.com")
os.environ.setdefault("CLIENT_BASE_URL", "https://console.example.com/")

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
def _jsonb_on_sqlite(type_, compiler, **kw):  # postgres-only type, unused by DOI
    return "JSON"


from app.main import app  # noqa: E402 - must be imported after the engine swap
from app.models import EmailVerificationCode, Member  # noqa: E402
from app.services import email_verification  # noqa: E402

# ...as must this, a postgres-only default SQLite cannot render.
Member.__table__.c.custom_attributes.server_default = None
database.Base.metadata.create_all(
    bind=database.engine, tables=[Member.__table__, EmailVerificationCode.__table__]
)

MEMBER_ID = uuid.uuid4()
HEADERS = {"Authorization": "Bearer test-token"}
client = TestClient(app, raise_server_exceptions=False)


def _trigger(doi_type: str):
    response = client.post(
        "/doi/trigger",
        json={"memberId": str(MEMBER_ID), "type": doi_type},
        headers=HEADERS,
    )
    return response.status_code, response.json()


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
    session.add(Member(id=MEMBER_ID, name="Page Member", email="page@example.com"))
    session.commit()
    session.close()

    failures = []
    original_send = resend.Emails.send
    original_base = email_verification.settings.client_base_url
    sent = []

    def recording_send(params, *_args, **_kwargs):
        sent.append(params)
        return {"id": f"email_{len(sent)}"}

    try:
        resend.Emails.send = recording_send

        status, body = _trigger("page")
        if status != 200:
            failures.append(f"page trigger answered {status} {body}, expected 200")
        if body.get("message") != "Verification link sent":
            failures.append(f"page trigger message was {body.get('message')!r}")
        if len(sent) != 1:
            failures.append(f"page trigger sent {len(sent)} emails, expected 1")

        # The email must carry a usable /verify link, in both the HTML and the
        # plain-text part (clients that render either must both work). The HTML
        # one is entity-escaped, so it is unescaped back before comparing.
        email = sent[-1]
        links = {}
        for part in ("html", "text"):
            marker = "https://console.example.com/verify?"
            rendered = unescape(email.get(part, ""))
            if marker not in rendered:
                failures.append(f"page email {part} part has no /verify link")
                continue
            links[part] = marker + rendered.split(marker)[1].split('"')[0].split()[0]

        if len(links) == 2 and links["html"] != links["text"]:
            failures.append(f"html and text parts link elsewhere: {links}")

        link = links.get("text", "")
        query = parse_qs(urlparse(link).query) if link else {}
        if query.get("memberId") != [str(MEMBER_ID)]:
            failures.append(f"link memberId was {query.get('memberId')}")
        code = (query.get("code") or [""])[0]
        if not code.isdigit():
            failures.append(f"link carried no numeric code (query={query})")

        # Same type while the code is live: nothing new goes out.
        again = _trigger("page")
        if again != (status, body):
            failures.append(f"re-trigger answered {again}, expected {(status, body)}")
        if len(sent) != 1:
            failures.append(f"re-trigger sent another email ({len(sent)} total)")

        # The other type is a different email, so it must issue a fresh code.
        code_status, code_body = _trigger("code")
        if code_status != 200:
            failures.append(f"switching to code answered {code_status} {code_body}")
        if len(sent) != 2:
            failures.append(
                f"switching type sent {len(sent)} emails in total, expected 2"
            )
        if "verify?" in sent[-1].get("text", ""):
            failures.append("the code email carried a page link")
        if len(_active_codes()) != 1:
            failures.append(f"expected 1 outstanding code, found {len(_active_codes())}")

        # The link's code is dead now that a code email superseded it...
        superseded = client.post(
            "/doi/verify",
            json={"memberId": str(MEMBER_ID), "code": code},
            headers=HEADERS,
        )
        if superseded.status_code != 400:
            failures.append(
                f"superseded link code answered {superseded.status_code}, expected 400"
            )

        # ...so go back to a page email and verify with the link it sends.
        session = database.SessionLocal()
        session.query(EmailVerificationCode).delete()
        session.commit()
        session.close()

        _trigger("page")
        link_code = parse_qs(urlparse(
            f"https://console.example.com/verify?"
            + sent[-1]["text"].split("/verify?")[1].split()[0]
        ).query)["code"][0]
        verified = client.post(
            "/doi/verify",
            json={"memberId": str(MEMBER_ID), "code": link_code},
            headers=HEADERS,
        )
        if verified.status_code != 200 or not verified.json().get("verified"):
            failures.append(
                f"verifying the linked code answered {verified.status_code} "
                f"{verified.text}"
            )

        # An unconfigured client base URL must fail loudly and persist nothing.
        session = database.SessionLocal()
        member = session.get(Member, MEMBER_ID)
        member.email_verified_at = None
        session.query(EmailVerificationCode).delete()
        session.commit()
        session.close()

        email_verification.settings = type(email_verification.settings)(
            **{
                **email_verification.settings.__dict__,
                "client_base_url": "",
            }
        )
        before = len(sent)
        unconfigured_status, _ = _trigger("page")
        if unconfigured_status != 500:
            failures.append(
                f"page trigger without CLIENT_BASE_URL answered "
                f"{unconfigured_status}, expected 500"
            )
        if len(sent) != before:
            failures.append("page trigger without CLIENT_BASE_URL still sent an email")
        if _active_codes():
            failures.append("page trigger without CLIENT_BASE_URL left a code row")
    finally:
        resend.Emails.send = original_send
        email_verification.settings = type(email_verification.settings)(
            **{**email_verification.settings.__dict__, "client_base_url": original_base}
        )

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print('OK: /doi/trigger type="page" mails a working /verify link')


if __name__ == "__main__":
    main()
