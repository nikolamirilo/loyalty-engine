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

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Member, MemberLoginCode
from app.services.email_sending import EmailDeliveryError, code_email_html, send_email

logger = logging.getLogger("uvicorn.error")

CODE_TTL = timedelta(minutes=10)
MAX_ATTEMPTS = 5


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def find_member_by_email(db: Session, email: str) -> Optional[Member]:
    return db.query(Member).filter(Member.email == email).first()


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_code(member_id, code: str) -> str:
    # "login:" prefix keeps this hash space distinct from DOI's, so the same
    # member+code pair never hashes the same way across the two flows.
    return hmac.new(
        settings.api_token.encode(), f"login:{member_id}:{code}".encode(), hashlib.sha256
    ).hexdigest()


def _latest_active_code(db: Session, member_id) -> Optional[MemberLoginCode]:
    return (
        db.query(MemberLoginCode)
        .filter(
            MemberLoginCode.member_id == member_id,
            MemberLoginCode.consumed_at.is_(None),
        )
        .order_by(MemberLoginCode.created_at.desc())
        .first()
    )


def _send_login_code(member: Member, code: str) -> None:
    ttl_minutes = int(CODE_TTL.total_seconds() // 60)
    send_email(
        member.email,
        subject="Your login code",
        text=f"Your login code is {code}. It expires in {ttl_minutes} minutes.",
        html=code_email_html(code, ttl_minutes, label="Your login code"),
    )


def _issue_and_send_code(db: Session, member: Member) -> None:
    """Ensure `member` has a usable, unexpired login code in their inbox.

    Mirrors ``email_verification.trigger_verification``'s "one outstanding
    code, re-send while unexpired is a no-op" behavior, minus the
    email-verified gate - a login code can always be (re-)requested.
    """
    latest = _latest_active_code(db, member.id)
    now = _now()
    if latest is not None and now <= _as_aware(latest.expires_at):
        return

    code = _generate_code()

    # Send before touching the DB: if delivery fails, nothing about the
    # member's login state should change - an orphaned code row would
    # suppress every retry until it expired, for a code never delivered.
    try:
        _send_login_code(member, code)
    except EmailDeliveryError as exc:
        logger.exception(
            "Auth: could not send login code for member %s (from=%s): %s",
            member.id,
            settings.doi_from_email,
            exc.reason,
        )
        if exc.transient:
            raise HTTPException(
                502, "Could not send the login code. Please try again shortly."
            ) from exc
        raise HTTPException(
            500,
            f"Login code could not be sent - email delivery is misconfigured. {exc.reason}",
        ) from exc

    db.query(MemberLoginCode).filter(
        MemberLoginCode.member_id == member.id,
        MemberLoginCode.consumed_at.is_(None),
    ).delete()
    db.add(
        MemberLoginCode(
            member_id=member.id,
            code_hash=_hash_code(member.id, code),
            expires_at=now + CODE_TTL,
        )
    )
    db.commit()


def trigger_signup(db: Session, email: str, name: str, phone: Optional[str]) -> None:
    if find_member_by_email(db, email) is not None:
        raise HTTPException(400, "An account with this email already exists. Log in instead.")

    member = Member(name=name, email=email, phone=phone)
    db.add(member)
    db.commit()
    db.refresh(member)

    _issue_and_send_code(db, member)


def trigger_login(db: Session, email: str) -> None:
    member = find_member_by_email(db, email)
    if member is None:
        raise HTTPException(404, "No account found for this email. Sign up instead.")

    _issue_and_send_code(db, member)


def verify_login_code(db: Session, email: str, code: str) -> Member:
    member = find_member_by_email(db, email)
    if member is None:
        raise HTTPException(404, "No account found for this email.")

    row = _latest_active_code(db, member.id)
    if row is None:
        raise HTTPException(400, "No active login code for this member")
    if _now() > _as_aware(row.expires_at):
        raise HTTPException(400, "Login code has expired")

    if not secrets.compare_digest(row.code_hash, _hash_code(member.id, code)):
        row.attempts += 1
        if row.attempts >= MAX_ATTEMPTS:
            row.consumed_at = _now()
        db.commit()
        raise HTTPException(400, "Invalid login code")

    row.consumed_at = _now()
    db.commit()
    return member
