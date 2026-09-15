"""Segment lookups."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Program, Segment
from app.services.scoping import get_scoped_or_404


def get_segment_or_404(db: Session, segment_id: UUID, program: Program) -> Segment:
    return get_scoped_or_404(db, Segment, segment_id, program, "Segment")
