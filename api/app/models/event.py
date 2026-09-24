import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:  # relationship targets, resolved by SQLAlchemy's class registry
    from app.models.member import Member


class EventType(Base):
    """Something a member does that an outside system reports, e.g. "Order placed".

    Events must be defined before they are accepted, so a typo in an
    integration fails loudly instead of silently earning nothing. ``key`` is
    what callers send as the event ``type``; like a member attribute key it is
    derived from the name once and never changes.

    ``attributes`` is the event's payload schema, a list of
    ``{key, label, type, options}`` using the member attribute types.
    """

    __tablename__ = "event_types"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    attributes: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("program_id", "key", name="uq_program_event_type_key"),)

    rules: Mapped[List["EventRule"]] = relationship(
        "EventRule",
        back_populates="event_type",
        order_by="EventRule.created_at",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class EventRule(Base):
    """What an event does: if every condition matches, every effect runs.

    ``conditions`` and ``effects`` are JSON lists validated on write by
    ``app.services.rules``, so a rule that points at a missing reward or
    attribute fails when it is saved rather than when an event arrives.
    """

    __tablename__ = "event_rules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    event_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("event_types.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    conditions: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    effects: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    # How many times one member can trigger this rule. Null means every time.
    limit_per_member: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    event_type: Mapped["EventType"] = relationship("EventType", back_populates="rules")


class MemberEvent(Base):
    """One event received for a member, with what its rules did.

    ``type`` is a copy of the event type's key, so history survives the
    definition being deleted (the same reason ``Purchase`` copies the product
    name). ``effects`` records each applied or skipped effect as shown in the
    console. ``external_id`` is the caller's own event id: sending the same one
    twice returns the first result instead of applying the rules again.
    """

    __tablename__ = "member_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("event_types.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String, nullable=False)
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    effects: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    external_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("member_id", "external_id", name="uq_member_event_external_id"),)

    member: Mapped["Member"] = relationship("Member")
    event_type: Mapped[Optional["EventType"]] = relationship("EventType")

    @property
    def name(self) -> str:
        """The event type's current name, or its key once the type is deleted."""
        return self.event_type.name if self.event_type else self.type


class EventRuleRun(Base):
    """One time a rule fired for a member. Counted to enforce ``limit_per_member``."""

    __tablename__ = "event_rule_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("event_rules.id", ondelete="CASCADE"), nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("members.id", ondelete="CASCADE"), nullable=False
    )
    member_event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("member_events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("ix_event_rule_runs_rule_member", "rule_id", "member_id"),)
