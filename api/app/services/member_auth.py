"""Member login via emailed one-time code.

Independent of DOI (``email_verification.py``): DOI proves a member owns an
address once, permanently (``member.email_verified_at``). This flow proves it
on every sign-in and never touches that field - a member can be logged out,
come back next week, and request a fresh code without DOI's "already
verified" 409 getting in the way.
"""

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import InvalidInput, Misconfigured, NotFound, UpstreamError
from app.core.program import default_program
from app.models import Member, MemberIdentity, MemberLoginCode
from app.integrations.email import EmailDeliveryError, send_email
from app.services.code_emails import code_email_html, enforce_resend_cooldown
from app.services.memberships import enrol_everywhere, join

logger = logging.getLogger("uvicorn.error")

CODE_TTL = timedelta(minutes=10)
MAX_ATTEMPTS = 5


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def find_identity_by_email(db: Session, email: str) -> Optional[MemberIdentity]:
    return db.query(MemberIdentity).filter(MemberIdentity.email == email).first()


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_code(identity_id, code: str) -> str:
    # "login:" prefix keeps this hash space distinct from DOI's, so the same
    # person+code pair never hashes the same way across the two flows.
    return hmac.new(
        settings.api_token.encode(), f"login:{identity_id}:{code}".encode(), hashlib.sha256
    ).hexdigest()


def _latest_active_code(db: Session, identity_id) -> Optional[MemberLoginCode]:
    return (
        db.query(MemberLoginCode)
        .filter(
            MemberLoginCode.identity_id == identity_id,
            MemberLoginCode.consumed_at.is_(None),
        )
        .order_by(MemberLoginCode.created_at.desc())
        .first()
    )


def _last_sent_at(db: Session, identity_id) -> Optional[datetime]:
    # A code they signed in with doesn't count: it did its job, and signing in
    # again (another device, right after logging out) is a new request, not a
    # resend. A code burned through MAX_ATTEMPTS wrong guesses does count.
    row = (
        db.query(MemberLoginCode.created_at)
        .filter(
            MemberLoginCode.identity_id == identity_id,
            or_(
                MemberLoginCode.consumed_at.is_(None),
                MemberLoginCode.attempts >= MAX_ATTEMPTS,
            ),
        )
        .order_by(MemberLoginCode.created_at.desc())
        .first()
    )
    return row.created_at if row else None


def _send_login_code(identity: MemberIdentity, code: str) -> None:
    ttl_minutes = int(CODE_TTL.total_seconds() // 60)
    send_email(
        identity.email,
        subject="Your login code",
        text=f"Your login code is {code}. It expires in {ttl_minutes} minutes.",
        html=code_email_html(code, ttl_minutes, label="Your login code"),
    )


def _issue_and_send_code(db: Session, identity: MemberIdentity) -> None:
    """Mail `identity` a fresh login code, retiring any previous one.

    Mirrors ``email_verification.trigger_verification``: every request sends a
    new code (only hashes are stored, so the old one can't be re-sent), and
    requests closer together than RESEND_COOLDOWN answer 429. There is no
    email-verified gate - a login code can always be requested.

    Keyed to the person, not to one of their memberships: the code proves who
    is signing in, and the program they land in comes from the request.
    """
    now = _now()
    enforce_resend_cooldown(_last_sent_at(db, identity.id), now)

    code = _generate_code()

    # Send before touching the DB: if delivery fails, nothing about the
    # member's login state should change - the old code stays valid, and no
    # row is written to start a cooldown for an email that never went out.
    try:
        _send_login_code(identity, code)
    except EmailDeliveryError as exc:
        logger.exception(
            "Auth: could not send login code for identity %s (from=%s): %s",
            identity.id,
            settings.EMAIL_FROM,
            exc.reason,
        )
        if exc.transient:
            raise UpstreamError(
                "Could not send the login code. Please try again shortly."
            ) from exc
        raise Misconfigured(
            f"Login code could not be sent - email delivery is misconfigured. {exc.reason}",
        ) from exc

    db.query(MemberLoginCode).filter(
        MemberLoginCode.identity_id == identity.id,
        MemberLoginCode.consumed_at.is_(None),
    ).delete()
    db.add(
        MemberLoginCode(
            identity_id=identity.id,
            code_hash=_hash_code(identity.id, code),
            expires_at=now + CODE_TTL,
        )
    )
    db.commit()


def trigger_signup(db: Session, email: str, name: str, phone: Optional[str]) -> None:
    identity = find_identity_by_email(db, email)
    if identity is not None:
        # Members are global, so an existing person already holds a membership
        # in every program - including this one. There is nothing to sign up to.
        raise InvalidInput("An account with this email already exists. Log in instead.")

    identity = MemberIdentity(name=name, email=email, phone=phone)
    db.add(identity)
    db.flush()
    # One membership per program, not just the one they signed up through.
    enrol_everywhere(db, identity)
    db.commit()

    _issue_and_send_code(db, identity)


def trigger_login(db: Session, email: str) -> None:
    identity = find_identity_by_email(db, email)
    if identity is None:
        raise NotFound("No account found for this email. Sign up instead.")

    # Everyone is enrolled everywhere already; this only repairs a person who
    # predates a program, so they can sign into it like anyone else.
    if enrol_everywhere(db, identity):
        db.commit()

    _issue_and_send_code(db, identity)


def verify_login_code(db: Session, email: str, code: str) -> Member:
    identity = find_identity_by_email(db, email)
    if identity is None:
        raise NotFound("No account found for this email.")

    row = _latest_active_code(db, identity.id)
    if row is None:
        raise InvalidInput("No active login code for this member")
    if _now() > _as_aware(row.expires_at):
        raise InvalidInput("Login code has expired")

    if not secrets.compare_digest(row.code_hash, _hash_code(identity.id, code)):
        row.attempts += 1
        if row.attempts >= MAX_ATTEMPTS:
            row.consumed_at = _now()
        db.commit()
        raise InvalidInput("Invalid login code")

    row.consumed_at = _now()
    # The code proves who they are. Signing in always lands in the default
    # program - the member switches from there - so that is the membership
    # handed back. It already exists; join() just picks it.
    member = join(db, default_program(db), identity)
    db.commit()
    db.refresh(member)
    return member
