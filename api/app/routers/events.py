from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session, contains_eager, joinedload

from app.core.database import get_db
from app.core.program import get_program
from app.models import Member, MemberEvent, Program
from app.schemas import EventLogOut, MemberEventOut, TrackEventRequest
from app.services.events import track_event
from app.services.scoping import get_scoped_or_404

router = APIRouter(tags=["Events"])


@router.post("/events", response_model=MemberEventOut, status_code=201)
def receive_event(
    body: TrackEventRequest,
    response: Response,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    """Record an event for a member and run its rules.

    The response lists every effect the matching rules applied or skipped.
    Sending an `eventId` this member already has returns that first event
    with 200 instead of 201, and runs nothing again.
    """
    event, created = track_event(db, program, body)
    if not created:
        response.status_code = 200
    return event


@router.get("/events", response_model=list[EventLogOut])
def list_events(
    type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    """Every event received in the program, newest first, with the member it
    was for. `type` narrows it to one event type's key."""
    q = (
        db.query(MemberEvent)
        .join(Member, MemberEvent.member_id == Member.id)
        .options(
            joinedload(MemberEvent.event_type),
            contains_eager(MemberEvent.member).joinedload(Member.identity),
        )
        .filter(Member.program_id == program.id)
    )
    if type:
        q = q.filter(MemberEvent.type == type)
    return q.order_by(MemberEvent.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/members/{member_id}/events", response_model=list[MemberEventOut])
def list_member_events(
    member_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    # Resolving the member inside the program scopes the rows below: events
    # hang off the membership, so they can't belong to another program.
    get_scoped_or_404(db, Member, member_id, program, "Member")
    return (
        db.query(MemberEvent)
        .options(joinedload(MemberEvent.event_type))
        .filter(MemberEvent.member_id == member_id)
        .order_by(MemberEvent.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
