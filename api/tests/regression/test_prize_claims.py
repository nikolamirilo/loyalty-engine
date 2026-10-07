"""Regression test for prize emails and claiming.

What this guards:

  * Assigning a prize without a body still works and sends nothing.
  * `sendEmail: true` mails a claim link to the client's
    `/p/{programSlug}/claim` page, in both the HTML and the text part, and the
    prize's name is escaped in the HTML.
  * The link's token resolves to the prize's own program whatever
    X-Program-Id says, so a link can't be claimed into another program.
  * Claiming by token marks the prize claimed, and claiming again changes
    nothing. An unknown token is a 404; an expired, unclaimed one is a 400,
    and the member can still claim it from the wallet endpoint.
  * Only assigned prizes can be claimed, and only inside their own program.
  * A failed or unconfigured email leaves the prize assigned and says why.

Runs against an in-memory SQLite database with the Resend SDK stubbed out, so
it never touches Supabase and never sends mail.

Run: ./venv/bin/python -m tests.regression.test_prize_claims
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import parse_qs, urlparse

os.environ.setdefault("DATABASE_URL", "postgresql://u:p@h:6543/postgres")
os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("RESEND_API_KEY", "test-resend-key")
os.environ.setdefault("DOI_FROM_EMAIL", "noreply@example.com")
os.environ.setdefault("CLIENT_BASE_URL", "https://app.example.com/")

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
    MemberAttribute,
    MemberIdentity,
    Program,
    Redemption,
    RedemptionSource,
    Reward,
)
from app.services import prize_claims  # noqa: E402

# ...as must these, postgres-only defaults SQLite cannot render.
Member.__table__.c.custom_attributes.server_default = None
MemberAttribute.__table__.c.options.server_default = None
database.Base.metadata.create_all(bind=database.engine)

DEFAULT_PROGRAM_ID = uuid.uuid4()
OTHER_PROGRAM_ID = uuid.uuid4()
IDENTITY_ID = uuid.uuid4()
DEFAULT_MEMBER_ID = uuid.uuid4()
MEMBER_ID = uuid.uuid4()  # the membership in the *non-default* program
REWARD_ID = uuid.uuid4()
REWARD_NAME = "Coffee <b>&</b> cake"
AUTH = {"Authorization": "Bearer test-token"}
OTHER = {**AUTH, "X-Program-Id": "other"}
client = TestClient(app, raise_server_exceptions=False)

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def assign(send_email: bool | None = None):
    body = None if send_email is None else {"sendEmail": send_email}
    return client.post(f"/members/{MEMBER_ID}/prizes/{REWARD_ID}", json=body, headers=OTHER)


def link_in(email: dict, part: str) -> str:
    marker = "https://app.example.com/p/other/claim?"
    rendered = unescape(email.get(part, ""))
    if marker not in rendered:
        return ""
    return marker + rendered.split(marker)[1].split('"')[0].split()[0]


def token_of(link: str) -> str:
    return (parse_qs(urlparse(link).query).get("token") or [""])[0]


def main() -> None:
    session = database.SessionLocal()
    session.add(Program(id=DEFAULT_PROGRAM_ID, name="Default", slug="default", is_default=True))
    session.add(Program(id=OTHER_PROGRAM_ID, name="Other", slug="other", primary_color="#123456"))
    session.add(MemberIdentity(id=IDENTITY_ID, name="Prize Member", email="prize@example.com"))
    session.add(Member(id=DEFAULT_MEMBER_ID, program_id=DEFAULT_PROGRAM_ID, identity_id=IDENTITY_ID))
    session.add(Member(id=MEMBER_ID, program_id=OTHER_PROGRAM_ID, identity_id=IDENTITY_ID))
    session.add(
        Reward(
            id=REWARD_ID,
            program_id=OTHER_PROGRAM_ID,
            name=REWARD_NAME,
            description="A treat",
            points_cost=100,
        )
    )
    session.commit()
    session.close()

    original_send = resend.Emails.send
    original_settings = prize_claims.settings
    sent: list[dict] = []

    def recording_send(params, *_args, **_kwargs):
        sent.append(params)
        return {"id": f"email_{len(sent)}"}

    try:
        resend.Emails.send = recording_send

        # No body: the endpoint behaves as it always did.
        plain = assign()
        check(plain.status_code == 201, f"assign without body answered {plain.status_code} {plain.text}")
        check(plain.json().get("claimedAt") is None, "a new prize was already claimed")
        check(plain.json().get("emailSent") is False, "assign without body reported an email")
        check(not sent, "assign without body sent an email")

        # sendEmail: a branded email with a working claim link.
        emailed = assign(True)
        body = emailed.json()
        check(emailed.status_code == 201, f"assign with email answered {emailed.status_code} {emailed.text}")
        check(body.get("emailSent") is True, f"emailSent was {body.get('emailSent')}: {body.get('emailError')}")
        check(len(sent) == 1, f"assign with email sent {len(sent)} emails, expected 1")
        email = sent[-1] if sent else {}
        html_link, text_link = link_in(email, "html"), link_in(email, "text")
        check(bool(html_link) and html_link == text_link, f"html/text links differ or missing: {html_link!r} {text_link!r}")
        check("Coffee &lt;b&gt;&amp;&lt;/b&gt; cake" in email.get("html", ""), "reward name was not escaped in the HTML")
        check("#123456" in email.get("html", ""), "email did not use the program's colour")
        token = token_of(text_link)
        check(len(token) > 20, f"link carried no token: {text_link!r}")

        # The token decides the program, not the header.
        preview = client.get(f"/prizes/claim/{token}", headers={**AUTH, "X-Program-Id": "default"})
        check(preview.status_code == 200, f"preview answered {preview.status_code} {preview.text}")
        p = preview.json()
        check(p.get("program", {}).get("slug") == "other", f"preview program was {p.get('program')}")
        check(p.get("redemptionId") == body.get("id"), "preview named a different prize")
        check(p.get("claimedAt") is None and p.get("expired") is False, f"preview state was {p}")
        check(p.get("memberName") == "Prize Member", f"preview memberName was {p.get('memberName')}")

        claimed = client.post("/prizes/claim", json={"token": token}, headers=AUTH)
        check(claimed.status_code == 200, f"claim answered {claimed.status_code} {claimed.text}")
        first_claimed_at = claimed.json().get("claimedAt")
        check(first_claimed_at is not None, "claim did not set claimedAt")
        again = client.post("/prizes/claim", json={"token": token}, headers=AUTH)
        check(again.status_code == 200, f"second claim answered {again.status_code}")
        check(again.json().get("claimedAt") == first_claimed_at, "second claim moved claimedAt")

        unknown = client.post("/prizes/claim", json={"token": "nope"}, headers=AUTH)
        check(unknown.status_code == 404, f"unknown token answered {unknown.status_code}")

        # An expired link refuses, but the wallet can still claim.
        expiring = assign(True).json()
        expiring_token = token_of(link_in(sent[-1], "text"))
        session = database.SessionLocal()
        session.get(Redemption, uuid.UUID(expiring["id"])).claim_token_expires_at = (
            datetime.now(timezone.utc) - timedelta(days=1)
        )
        session.commit()
        session.close()
        check(
            client.get(f"/prizes/claim/{expiring_token}", headers=AUTH).json().get("expired") is True,
            "an expired link previewed as not expired",
        )
        expired = client.post("/prizes/claim", json={"token": expiring_token}, headers=AUTH)
        check(expired.status_code == 400, f"expired link claim answered {expired.status_code}")

        wrong_program = client.post(
            f"/members/{MEMBER_ID}/prizes/{expiring['id']}/claim", headers=AUTH
        )
        check(wrong_program.status_code == 404, f"claim in the wrong program answered {wrong_program.status_code}")
        wallet = client.post(f"/members/{MEMBER_ID}/prizes/{expiring['id']}/claim", headers=OTHER)
        check(wallet.status_code == 200, f"wallet claim answered {wallet.status_code} {wallet.text}")
        check(wallet.json().get("claimedAt") is not None, "wallet claim did not set claimedAt")

        # Only assigned prizes are claimable.
        session = database.SessionLocal()
        bought = Redemption(
            member_id=MEMBER_ID, reward_id=REWARD_ID, points_spent=100, source=RedemptionSource.redeemed
        )
        session.add(bought)
        session.commit()
        bought_id = bought.id
        session.close()
        redeemed = client.post(f"/members/{MEMBER_ID}/prizes/{bought_id}/claim", headers=OTHER)
        check(redeemed.status_code == 400, f"claiming a redeemed reward answered {redeemed.status_code}")

        # A failed send keeps the prize and says why.
        def failing_send(*_args, **_kwargs):
            raise RuntimeError("provider down")

        resend.Emails.send = failing_send
        failed = assign(True)
        check(failed.status_code == 201, f"assign with failing email answered {failed.status_code}")
        check(failed.json().get("emailSent") is False, "a failed email reported as sent")
        check("provider down" in (failed.json().get("emailError") or ""), f"emailError was {failed.json().get('emailError')}")

        # So does a deployment without CLIENT_BASE_URL.
        resend.Emails.send = recording_send
        prize_claims.settings = type(original_settings)(
            **{**original_settings.__dict__, "client_base_url": ""}
        )
        before = len(sent)
        unconfigured = assign(True)
        check(unconfigured.status_code == 201, f"assign without CLIENT_BASE_URL answered {unconfigured.status_code}")
        check("CLIENT_BASE_URL" in (unconfigured.json().get("emailError") or ""), "missing CLIENT_BASE_URL not reported")
        check(len(sent) == before, "an email went out without CLIENT_BASE_URL")
    finally:
        resend.Emails.send = original_send
        prize_claims.settings = original_settings

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("OK: prize emails link to a working, program-routed claim page")


if __name__ == "__main__":
    main()
