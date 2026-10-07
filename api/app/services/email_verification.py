"""DOI (double opt-in) email verification.

A member proves ownership of their email by entering a short-lived numeric
code sent to it. Only a hash of the code is ever persisted
(``EmailVerificationCode.code_hash``); the raw code exists only in memory
long enough to be emailed.
"""

import hashlib
import hmac
import html
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import Conflict, InvalidInput, Misconfigured, NotFound, UpstreamError
from app.models import DOIType, EmailVerificationCode, Member, MemberIdentity
from app.integrations.email import EmailDeliveryError, send_email
from app.services.code_emails import (
    CODE_FG,
    FAINT,
    MUTED,
    PRIMARY,
    PRIMARY_FG,
    code_email_html,
    email_shell,
    enforce_resend_cooldown,
    expiry_note,
)

logger = logging.getLogger("uvicorn.error")

CODE_TTL = timedelta(minutes=10)
MAX_ATTEMPTS = 5


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    # Timestamps read back from the DB may be naive; stored values are UTC.
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def resolve_member(db: Session, email: Optional[str], member_id: Optional[UUID]) -> Member:
    """Look up the person a DOI request refers to, in whichever program.

    Exactly one of `email`/`member_id` is required; if both are given they
    must resolve to the same person, so a caller can't be misdirected by a
    stale/mismatched pair.

    Deliberately not scoped to a program. Every member belongs to every
    program and verification is stamped on the identity, so any of a person's
    member ids - from any program - names the same thing. Scoping it made a
    link issued from one program answer "Member not found" when opened in
    another. A membership is still returned (rather than the identity) because
    the `link` email needs a member id to address the client's /verify page.
    """
    if email is None and member_id is None:
        raise InvalidInput("Provide either email or member_id")

    if member_id is not None:
        member = db.get(Member, member_id)
        if not member:
            raise NotFound("Member not found")
        if email is not None and member.email.lower() != email.lower():
            raise InvalidInput("email and member_id do not refer to the same member")
        return member

    member = db.query(Member).join(Member.identity).filter(MemberIdentity.email == email).first()
    if not member:
        raise NotFound("Member not found")
    return member


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_code(identity_id: UUID, code: str) -> str:
    # Salted with identity_id (via HMAC key = the existing shared API_TOKEN
    # secret) so the same code never hashes the same way across people.
    return hmac.new(
        settings.api_token.encode(), f"{identity_id}:{code}".encode(), hashlib.sha256
    ).hexdigest()


def _latest_active_code(db: Session, identity_id: UUID) -> Optional[EmailVerificationCode]:
    return (
        db.query(EmailVerificationCode)
        .filter(
            EmailVerificationCode.identity_id == identity_id,
            EmailVerificationCode.consumed_at.is_(None),
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .first()
    )


def _last_sent_at(db: Session, identity_id: UUID) -> Optional[datetime]:
    # Any code counts, used or not: a successfully used one means the email is
    # verified, which trigger_verification refuses before this is consulted.
    row = (
        db.query(EmailVerificationCode.created_at)
        .filter(EmailVerificationCode.identity_id == identity_id)
        .order_by(EmailVerificationCode.created_at.desc())
        .first()
    )
    return row.created_at if row else None


def _link_email_html(link: str, ttl_minutes: int) -> str:
    # A bulletproof-ish button: a padded <a> inside its own table cell, which
    # is what email clients render consistently. The raw URL is repeated below
    # it for clients that strip links or open in a different browser.
    #
    # Escaped because the link's `&` separator is markup in HTML: an unescaped
    # `&code=` is a parse error that strict clients may swallow, taking the code
    # out of the URL with it.
    link = html.escape(link, quote=True)
    return email_shell(
        f"""\
                <p style="margin:0 0 8px;font-size:14px;color:{MUTED};">Confirm your email address</p>
                <table role="presentation" align="center" cellpadding="0" cellspacing="0" style="margin:24px auto;">
                  <tr>
                    <td align="center" style="background-color:{PRIMARY};border-radius:10px;">
                      <a href="{link}" style="display:inline-block;padding:14px 32px;font-size:15px;font-weight:600;color:{PRIMARY_FG};text-decoration:none;">Verify my email</a>
                    </td>
                  </tr>
                </table>
                <p style="margin:16px 0 0;font-size:12px;color:{FAINT};word-break:break-all;">
                  Or paste this address into your browser:<br />
                  <a href="{link}" style="color:{CODE_FG};">{link}</a>
                </p>
{expiry_note("link", ttl_minutes)}"""
    )


def _verify_link(member_id: UUID, code: str) -> str:
    """The verification link for this member and code.

    It addresses the client's /verify page, which is the only thing that knows
    how to turn a press into a /doi/verify call. Raises if the client's base
    URL was never configured: without it there is no link to send, and an email
    with a broken button is worse than a clear failure.
    """
    base = settings.client_base_url
    if not base:
        raise Misconfigured(
            'Verification emails of type "link" need CLIENT_BASE_URL set to the '
            "public base URL of the client app.",
        )
    query = urlencode({"memberId": str(member_id), "code": code})
    return f"{base}/verify?{query}"


def _verification_email(member: Member, code: str, doi_type: DOIType) -> dict:
    """The provider payload for the email this DOI type calls for."""
    ttl_minutes = int(CODE_TTL.total_seconds() // 60)
    if doi_type is DOIType.link:
        link = _verify_link(member.id, code)
        return {
            "subject": "Confirm your email address",
            "text": (
                f"Confirm your email address by opening {link} and pressing "
                f"Verify my email. The link expires in {ttl_minutes} minutes."
            ),
            "html": _link_email_html(link, ttl_minutes),
        }
    return {
        "subject": "Your verification code",
        "text": f"Your verification code is {code}. It expires in {ttl_minutes} minutes.",
        "html": code_email_html(code, ttl_minutes),
    }


def _send_verification_email(member: Member, code: str, doi_type: DOIType) -> None:
    # Built before the call: a misconfigured CLIENT_BASE_URL is a deployment
    # error with its own answer, not a delivery failure to be reclassified as
    # "try again shortly" by send_email's error handling.
    payload = _verification_email(member, code, doi_type)
    send_email(member.email, payload["subject"], payload["text"], payload["html"])


def trigger_verification(
    db: Session, member: Member, doi_type: DOIType = DOIType.code
) -> None:
    """Mail the member a fresh verification email.

    ``doi_type`` picks which email that is: ``code`` mails a 6-digit code to
    type back, ``link`` mails a link to the client's /verify page that submits
    the code for them.

    Every trigger sends a new code and retires the previous one, so a member who
    lost or never got the first email can simply ask again. The same code can't
    be re-sent instead: only its hash is stored. The newest email is the one
    that works, which is also the one on top of their inbox.

    Triggers closer together than RESEND_COOLDOWN answer 429 and send nothing.
    """
    identity = member.identity
    if identity.email_verified_at is not None:
        raise Conflict("Member email is already verified")

    now = _now()
    enforce_resend_cooldown(_last_sent_at(db, identity.id), now)

    code = _generate_code()

    # Send before touching the DB: if delivery fails, nothing about the member's
    # verification state should change - the old code stays valid, and no row
    # is written to start a cooldown for an email that never went out.
    try:
        _send_verification_email(member, code, doi_type)
    except EmailDeliveryError as exc:
        # Log the provider's own words. Without this the endpoint answers with
        # a generic failure forever and the actual cause never reaches the logs.
        logger.exception(
            "DOI: could not send verification email for member %s (from=%s): %s",
            member.id,
            settings.EMAIL_FROM,
            exc.reason,
        )
        if exc.transient:
            raise UpstreamError(
                "Could not send the verification email. Please try again shortly."
            ) from exc
        # Permanent: retrying is pointless, so say what actually needs fixing.
        raise Misconfigured(
            "Verification email could not be sent - email delivery is "
            f"misconfigured. {exc.reason}",
        ) from exc

    # A person should only ever have one outstanding code at a time, so the
    # new one replaces whatever the previous email carried.
    db.query(EmailVerificationCode).filter(
        EmailVerificationCode.identity_id == identity.id,
        EmailVerificationCode.consumed_at.is_(None),
    ).delete()
    db.add(
        EmailVerificationCode(
            identity_id=identity.id,
            code_hash=_hash_code(identity.id, code),
            type=doi_type,
            expires_at=now + CODE_TTL,
        )
    )
    db.commit()


def verify_code(db: Session, member: Member, code: str) -> Member:
    identity = member.identity
    if identity.email_verified_at is not None:
        return member

    row = _latest_active_code(db, identity.id)
    if row is None:
        raise InvalidInput("No active verification code for this member")
    if _now() > _as_aware(row.expires_at):
        raise InvalidInput("Verification code has expired")

    if not secrets.compare_digest(row.code_hash, _hash_code(identity.id, code)):
        row.attempts += 1
        if row.attempts >= MAX_ATTEMPTS:
            row.consumed_at = _now()
        db.commit()
        raise InvalidInput("Invalid verification code")

    row.consumed_at = _now()
    # Stamped on the identity, so the person counts as verified in every
    # program they have joined, not just the one this request addressed.
    identity.email_verified_at = _now()
    db.commit()
    db.refresh(identity)
    return member
