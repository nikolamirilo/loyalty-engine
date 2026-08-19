"""Segment lookups."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Segment


def get_segment_or_404(db: Session, segment_id: UUID) -> Segment:
    segment = db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(404, "Segment not found")
    return segment
