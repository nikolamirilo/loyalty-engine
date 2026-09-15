"""Joining a program.

A person (``MemberIdentity``) holds one ``Member`` row per program they have
joined, and that row is where their points, tier and progress live. Creating
one is needed from two unrelated places - signing in, and switching program
from the member app - so it lives here rather than in either of them.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models import Member, MemberIdentity, Program
from app.services.custom_attributes import defaults_for_new_member
from app.services.tiers import apply_tier


def find_membership(
    db: Session, program: Program, identity: MemberIdentity
) -> Optional[Member]:
    return (
        db.query(Member)
        .filter(Member.identity_id == identity.id, Member.program_id == program.id)
        .first()
    )


def enrol(db: Session, program: Program, identity: MemberIdentity) -> Member:
    """Give `identity` a membership in `program`, seeded like a new member.

    Joining starts from zero: the person is shared, everything describing
    their standing in this program is not. The caller commits.
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


def join(db: Session, program: Program, identity: MemberIdentity) -> Member:
    """The identity's membership in `program`, created if they had none."""
    return find_membership(db, program, identity) or enrol(db, program, identity)
