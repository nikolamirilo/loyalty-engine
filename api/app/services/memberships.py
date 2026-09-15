"""Membership: who belongs to which program.

Members are global. A person (``MemberIdentity``) belongs to *every* program,
and holds one ``Member`` row per program which is where their points, tier and
progress live. The person is shared; their standing is not:

    lidl        member x - 1000 points, 3 rewards
    burger-king member x - nothing yet
    walter      member x - 2350 points, 5 rewards

"Not a member of burger-king" is not a state this model has. A person who has
never touched that program still has a membership there, sitting at zero. That
keeps a single rule - one row per person per program - which is what the
per-program RLS policies key on, and it means a new program is immediately
populated rather than filling up as people happen to sign in.

Holding that invariant means enrolling on both sides of the pair:

    a new person  -> a membership in every existing program  (`enrol_everywhere`)
    a new program -> a membership for every existing person  (`enrol_all_identities`)

Both are idempotent, so they are safe to re-run and safe to call from a path
that may already have enrolled someone. `backfill` repairs any drift.
"""

from typing import Optional
from uuid import UUID

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
    """The identity's membership in `program`, created if they had none.

    Every person is enrolled everywhere, so this normally just finds the row.
    It still creates one when missing, so a program added while a request was
    in flight cannot leave a caller without a membership.
    """
    return find_membership(db, program, identity) or enrol(db, program, identity)


def _programs_missing_for(db: Session, identity_id: UUID) -> list[Program]:
    joined = {
        m.program_id
        for m in db.query(Member.program_id).filter(Member.identity_id == identity_id).all()
    }
    return [p for p in db.query(Program).all() if p.id not in joined]


def enrol_everywhere(db: Session, identity: MemberIdentity) -> list[Member]:
    """Give `identity` a membership in every program they are missing one for.

    Called when a person first appears. The caller commits.
    """
    return [enrol(db, program, identity) for program in _programs_missing_for(db, identity.id)]


def enrol_all_identities(db: Session, program: Program) -> int:
    """Give every existing person a membership in `program`.

    Called when a program is created, so it opens already holding everyone
    rather than accumulating them as they sign in. Returns the number enrolled.
    The caller commits.

    The attribute defaults are read once rather than per person: they are a
    property of the program, so they are the same for every row written here.
    """
    enrolled = {
        m.identity_id
        for m in db.query(Member.identity_id).filter(Member.program_id == program.id).all()
    }
    identities = [i for i in db.query(MemberIdentity).all() if i.id not in enrolled]
    if not identities:
        return 0

    defaults = defaults_for_new_member(db, program.id)
    members = [
        Member(program_id=program.id, identity_id=i.id, custom_attributes=dict(defaults))
        for i in identities
    ]
    db.add_all(members)
    db.flush()
    # Everyone lands on zero points, so they all resolve to the same tier - but
    # it is the program's own lowest tier, which only apply_tier knows how to find.
    for member in members:
        apply_tier(db, member)
    return len(members)


def backfill(db: Session) -> int:
    """Enrol every person into every program they are missing.

    Repairs drift from rows written before members were global, or by any path
    that bypassed the services here. Returns the number of memberships created.
    The caller commits.
    """
    return sum(enrol_all_identities(db, program) for program in db.query(Program).all())
