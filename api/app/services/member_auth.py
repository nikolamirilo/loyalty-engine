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
from app.models import Member, MemberIdentity, MemberLoginCode, Program
from app.services.custom_attributes import defaults_for_new_member
from app.services.email_sending import EmailDeliveryError, code_email_html, send_email
from app.services.tiers import apply_tier

logger = logging.getLogger("uvicorn.error")

CODE_TTL = timedelta(minutes=10)
MAX_ATTEMPTS = 5


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def find_identity_by_email(db: Session, email: str) -> Optional[MemberIdentity]:
    return db.query(MemberIdentity).filter(MemberIdentity.email == email).first()


def find_membership(db: Session, program: Program, identity: MemberIdentity) -> Optional[Member]:
    return (
        db.query(Member)
        .filter(Member.identity_id == identity.id, Member.program_id == program.id)
        .first()
    )


def enrol(db: Session, program: Program, identity: MemberIdentity) -> Member:
    """Give `identity` a membership in `program`, seeded like a new member.

    Signing in with an email that exists but has never joined this program
    enrols the person rather than rejecting them: one test account is then
    usable across every demo without being recreated in each.
    """
    member = Member(
        program_id=program.id,
        identity_id=identity.id,
        custom_attributes=defaults_for_new_member(db, program.id),
    )
    db.add(member)
    db.flush()
    apply_tier(db, member)
    return member


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


def _send_login_code(identity: MemberIdentity, code: str) -> None:
    ttl_minutes = int(CODE_TTL.total_seconds() // 60)
    send_email(
        identity.email,
        subject="Your login code",
        text=f"Your login code is {code}. It expires in {ttl_minutes} minutes.",
        html=code_email_html(code, ttl_minutes, label="Your login code"),
    )


def _issue_and_send_code(db: Session, identity: MemberIdentity) -> None:
    """Ensure `identity` has a usable, unexpired login code in their inbox.

    Mirrors ``email_verification.trigger_verification``'s "one outstanding
    code, re-send while unexpired is a no-op" behavior, minus the
    email-verified gate - a login code can always be (re-)requested.

    Keyed to the person, not to one of their memberships: the code proves who
    is signing in, and the program they land in comes from the request.
    """
    latest = _latest_active_code(db, identity.id)
    now = _now()
    if latest is not None and now <= _as_aware(latest.expires_at):
        return

    code = _generate_code()

    # Send before touching the DB: if delivery fails, nothing about the
    # member's login state should change - an orphaned code row would
    # suppress every retry until it expired, for a code never delivered.
    try:
        _send_login_code(identity, code)
    except EmailDeliveryError as exc:
        logger.exception(
            "Auth: could not send login code for identity %s (from=%s): %s",
            identity.id,
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


def trigger_signup(
    db: Session, program: Program, email: str, name: str, phone: Optional[str]
) -> None:
    identity = find_identity_by_email(db, email)
    if identity is None:
        identity = MemberIdentity(name=name, email=email, phone=phone)
        db.add(identity)
        db.flush()
    elif find_membership(db, program, identity) is not None:
        raise HTTPException(400, "An account with this email already exists. Log in instead.")

    # The person may exist already from another program, in which case this
    # signs them up to this one rather than creating a second account.
    enrol(db, program, identity)
    db.commit()

    _issue_and_send_code(db, identity)


def trigger_login(db: Session, program: Program, email: str) -> None:
    identity = find_identity_by_email(db, email)
    if identity is None:
        raise HTTPException(404, "No account found for this email. Sign up instead.")

    if find_membership(db, program, identity) is None:
        enrol(db, program, identity)
        db.commit()

    _issue_and_send_code(db, identity)


def verify_login_code(db: Session, program: Program, email: str, code: str) -> Member:
    identity = find_identity_by_email(db, email)
    if identity is None:
        raise HTTPException(404, "No account found for this email.")

    row = _latest_active_code(db, identity.id)
    if row is None:
        raise HTTPException(400, "No active login code for this member")
    if _now() > _as_aware(row.expires_at):
        raise HTTPException(400, "Login code has expired")

    if not secrets.compare_digest(row.code_hash, _hash_code(identity.id, code)):
        row.attempts += 1
        if row.attempts >= MAX_ATTEMPTS:
            row.consumed_at = _now()
        db.commit()
        raise HTTPException(400, "Invalid login code")

    row.consumed_at = _now()
    # The code proves who they are; the program comes from the request, so a
    # member signing into a program they have not joined is enrolled here.
    member = find_membership(db, program, identity) or enrol(db, program, identity)
    db.commit()
    db.refresh(member)
    return member
