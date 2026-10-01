"""Creating, editing and summarising the members of a program.

A member is a person (``MemberIdentity``, shared by every program) plus their
membership in one program (``Member``). Enrolment itself, the one-row-per-
person-per-program rule, lives in ``app.services.memberships``.
"""

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.errors import InvalidInput
from app.models import Member, MemberIdentity, Program
from app.schemas import MemberCreate, MemberUpdate
from app.services.custom_attributes import defaults_for_new_member, validate_payload
from app.services.memberships import enrol_everywhere, find_membership
from app.services.segments import set_member_segments
from app.services.tiers import apply_tier

# Fields of `MemberUpdate` that belong to the person rather than to this
# membership, so a write lands on the identity and is visible in every program
# that person has joined.
PERSON_FIELDS = frozenset({"name", "email", "phone"})


def register_member(db: Session, program: Program, body: MemberCreate) -> Member:
    """Create a new person and return their membership in `program`.

    Members are global: a person exists once and belongs to every program, so
    there is no "add an existing person to this program" - they are already in
    it. A known email is therefore a duplicate, not an enrolment. To fill in
    the membership they already hold here, update it instead. The caller
    commits.
    """
    if db.query(MemberIdentity).filter(MemberIdentity.email == body.email).first():
        raise InvalidInput("A member with this email already exists")

    identity = MemberIdentity(name=body.name, email=body.email, phone=body.phone)
    db.add(identity)
    db.flush()
    enrol_everywhere(db, identity)
    member = find_membership(db, program, identity)

    # Definition defaults fill in only the attributes the caller didn't supply, so
    # a member created through the API lands with the same values an admin sees
    # prefilled in the console's create form. `enrol_everywhere` already seeded
    # the defaults; this layers the caller's own values over them.
    member.custom_attributes = {
        **defaults_for_new_member(db, program.id),
        **validate_payload(db, program.id, body.custom_attributes),
    }
    db.flush()
    set_member_segments(db, member, program, body.segment_ids)
    apply_tier(db, member)
    return member


def edit_member(db: Session, program: Program, member: Member, body: MemberUpdate) -> None:
    """Apply a partial update to `member` and the person behind it. The caller
    commits."""
    if body.email is not None and body.email != member.email:
        if (
            db.query(MemberIdentity)
            .filter(
                MemberIdentity.email == body.email,
                MemberIdentity.id != member.identity_id,
            )
            .first()
        ):
            raise InvalidInput("Email already registered")
    data = body.model_dump(
        exclude_none=True, exclude={"segment_ids", "custom_attributes", "email_verified"}
    )
    for field, value in data.items():
        setattr(member.identity if field in PERSON_FIELDS else member, field, value)
    if body.email_verified is not None:
        member.identity.email_verified_at = (
            datetime.now(timezone.utc) if body.email_verified else None
        )
    if body.custom_attributes is not None:
        # Shallow merge, not replace: a caller that knows about one attribute must
        # not wipe the others. A key sent as null clears just that value.
        # Reassignment (not in-place mutation) is what makes SQLAlchemy see the
        # change on a plain JSONB column.
        patch = validate_payload(db, program.id, body.custom_attributes)
        member.custom_attributes = {**(member.custom_attributes or {}), **patch}
    if body.segment_ids is not None:
        set_member_segments(db, member, program, body.segment_ids)
    # A tier's conditions can read segments or custom attributes, so either
    # changing can move the member into a different one.
    if body.segment_ids is not None or body.custom_attributes is not None:
        apply_tier(db, member)


def summarize_members(db: Session, program: Program) -> dict:
    """Dashboard aggregates computed server-side so the client doesn't download
    every member just to tally them: total count, points in circulation, and the
    member-count-per-tier distribution.

    Grouped by each member's stored ``tier_id`` rather than recomputed live: a
    tier's conditions can now reach beyond the points balance (purchase spend,
    segments, custom attributes), and `apply_tier` already re-runs on every
    change any of those can come from, plus whenever a tier definition itself
    changes (`app.services.tiers.reapply_tiers`). The stored value is always
    current, and grouping by it is one cheap query instead of re-evaluating
    every member's conditions on every dashboard load.
    """
    count = db.query(func.count(Member.id)).filter(Member.program_id == program.id).scalar() or 0
    points_in_circulation = (
        db.query(func.coalesce(func.sum(Member.total_points), 0))
        .filter(Member.program_id == program.id)
        .scalar()
        or 0
    )

    by_tier: dict[str, int] = {}
    untiered = 0
    for tier_id, tier_count in (
        db.query(Member.tier_id, func.count(Member.id))
        .filter(Member.program_id == program.id)
        .group_by(Member.tier_id)
        .all()
    ):
        if tier_id is None:
            untiered = tier_count
        else:
            by_tier[str(tier_id)] = tier_count

    return {
        "count": count,
        "points_in_circulation": points_in_circulation,
        "by_tier": by_tier,
        "untiered": untiered,
    }
