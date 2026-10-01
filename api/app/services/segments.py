"""Segment lookups and a member's segment memberships."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.models import Member, MemberSegment, Program, Segment
from app.services.challenges import sync_assignments_for_segments
from app.services.scoping import get_scoped_or_404


def get_segment_or_404(db: Session, segment_id: UUID, program: Program) -> Segment:
    return get_scoped_or_404(db, Segment, segment_id, program, "Segment")


def set_member_segments(
    db: Session, member: Member, program: Program, segment_ids: list[UUID]
) -> None:
    """Replace `member`'s segment memberships with exactly `segment_ids`, and
    hand them the challenges those segments carry.

    Diffs against the current assignments instead of recreating the whole
    collection: callers (e.g. the member edit form) resend the full segment
    list on every save, even when it hasn't changed, and a wholesale replace
    would insert new rows for unchanged segments before deleting the old ones,
    tripping the `uq_member_segment` unique constraint against itself. The
    caller commits.
    """
    unique_ids = set(segment_ids)
    if unique_ids:
        found = {
            s.id
            for s in db.query(Segment.id)
            .filter(Segment.id.in_(unique_ids), Segment.program_id == program.id)
            .all()
        }
        missing = unique_ids - found
        if missing:
            raise NotFound(f"Segment(s) not found: {', '.join(str(i) for i in missing)}")
    current = {sa.segment_id: sa for sa in member.segment_assignments}
    for segment_id, assignment in current.items():
        if segment_id not in unique_ids:
            member.segment_assignments.remove(assignment)
    for segment_id in unique_ids - current.keys():
        member.segment_assignments.append(MemberSegment(segment_id=segment_id))
    sync_assignments_for_segments(db, program, unique_ids, {member.id})
