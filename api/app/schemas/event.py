from datetime import datetime
from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import Field

from app.models.enums import MemberAttributeType
from app.schemas.base import CamelModel

# ── event types ──────────────────────────────────────────────────────────────


class EventAttributeIn(CamelModel):
    """One attribute of an event type.

    Leave ``key`` out for a new attribute: it is derived from the label, like a
    member attribute key. Send the key of an existing attribute to keep it; its
    key and type then stay as they are.
    """

    key: Optional[str] = None
    label: str = Field(min_length=1, max_length=100)
    type: MemberAttributeType
    options: Optional[List[str]] = None  # `select` only


class EventAttributeOut(CamelModel):
    key: str
    label: str
    type: MemberAttributeType
    options: Optional[List[str]] = None


class EventTypeCreate(CamelModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    attributes: List[EventAttributeIn] = Field(default_factory=list)


class EventTypeUpdate(CamelModel):
    """``key`` is deliberately absent: integrations send it, so it never changes."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    # Replaces the whole list. Keep an existing attribute by sending its key.
    attributes: Optional[List[EventAttributeIn]] = None


# ── rules ────────────────────────────────────────────────────────────────────

Operator = Literal["eq", "neq", "gt", "gte", "lt", "lte", "contains"]


class RuleCondition(CamelModel):
    """``field`` is a path: ``event.attributes.<key>``, ``member.pointsBalance``,
    ``member.tier`` (a tier id), ``member.segments`` (a segment id, with
    ``contains``) or ``member.customAttributes.<key>``."""

    field: str
    operator: Operator
    value: Any


class AddPointsEffect(CamelModel):
    """Earns a fixed number of ``points``, or the value of the number attribute
    named in ``fromAttribute``. Exactly one of the two is set."""

    type: Literal["addPoints"]
    points: Optional[int] = Field(default=None, gt=0)
    from_attribute: Optional[str] = None


class BurnPointsEffect(CamelModel):
    """Spends a fixed number of ``points``, or the value of the number
    attribute named in ``fromAttribute``. Exactly one of the two is set."""

    type: Literal["burnPoints"]
    points: Optional[int] = Field(default=None, gt=0)
    from_attribute: Optional[str] = None


class GrantRewardEffect(CamelModel):
    type: Literal["grantReward"]
    reward_id: UUID


class AssignChallengeEffect(CamelModel):
    type: Literal["assignChallenge"]
    challenge_id: UUID


class AddChallengeProgressEffect(CamelModel):
    """Adds a fixed ``amount`` (1 when neither is sent), or the value of the
    number attribute named in ``fromAttribute``."""

    type: Literal["addChallengeProgress"]
    challenge_id: UUID
    amount: Optional[int] = Field(default=None, gt=0)
    from_attribute: Optional[str] = None


class AddToSegmentEffect(CamelModel):
    type: Literal["addToSegment"]
    segment_id: UUID


class RemoveFromSegmentEffect(CamelModel):
    type: Literal["removeFromSegment"]
    segment_id: UUID


class MemberFieldUpdate(CamelModel):
    """One member field set by an ``updateMember`` effect.

    ``field`` is ``member.name``, ``member.phone`` or
    ``member.customAttributes.<key>``. The new value is copied from the event
    attribute named in ``fromAttribute``, or else is ``value`` (null clears it).
    """

    field: str
    value: Any = None
    from_attribute: Optional[str] = None


class UpdateMemberEffect(CamelModel):
    type: Literal["updateMember"]
    fields: List[MemberFieldUpdate] = Field(min_length=1)


RuleEffect = Annotated[
    Union[
        AddPointsEffect,
        BurnPointsEffect,
        GrantRewardEffect,
        AssignChallengeEffect,
        AddChallengeProgressEffect,
        AddToSegmentEffect,
        RemoveFromSegmentEffect,
        UpdateMemberEffect,
    ],
    Field(discriminator="type"),
]


class EventRuleCreate(CamelModel):
    name: str = Field(min_length=1, max_length=100)
    is_active: bool = True
    # All must match. No conditions means the rule runs on every event.
    conditions: List[RuleCondition] = Field(default_factory=list)
    effects: List[RuleEffect] = Field(min_length=1)
    # How many times one member can trigger the rule. Null means every time.
    limit_per_member: Optional[int] = Field(default=None, gt=0)


class EventRuleUpdate(CamelModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    conditions: Optional[List[RuleCondition]] = None
    effects: Optional[List[RuleEffect]] = Field(default=None, min_length=1)
    # Send null to remove the limit, so only a field that is present is applied.
    limit_per_member: Optional[int] = Field(default=None, gt=0)


class EventRuleOut(CamelModel):
    id: UUID
    event_type_id: UUID
    name: str
    is_active: bool
    conditions: List[RuleCondition]
    effects: List[RuleEffect]
    limit_per_member: Optional[int] = None
    created_at: datetime


class EventTypeOut(CamelModel):
    id: UUID
    key: str
    name: str
    description: Optional[str] = None
    is_active: bool
    attributes: List[EventAttributeOut]
    rules: List[EventRuleOut] = Field(default_factory=list)
    created_at: datetime


# ── received events ──────────────────────────────────────────────────────────


class TrackEventRequest(CamelModel):
    member_id: UUID
    type: str  # an event type key, e.g. "orderPlaced"
    attributes: Dict[str, Any] = Field(default_factory=dict)
    # The caller's own id for this event. Sending it again returns the first
    # result instead of running the rules twice, so retries are safe.
    event_id: Optional[str] = Field(default=None, min_length=1, max_length=200)


class AppliedEffectOut(CamelModel):
    rule_id: UUID
    rule_name: str
    type: str
    summary: str  # e.g. "Earned 45 points"
    skipped: bool = False
    points: Optional[int] = None  # signed, like the ledger: burned points are negative
    reward_id: Optional[UUID] = None


class MemberEventOut(CamelModel):
    id: UUID
    member_id: UUID
    type: str
    name: str
    attributes: Dict[str, Any]
    effects: List[AppliedEffectOut]
    event_id: Optional[str] = Field(default=None, validation_alias="external_id")
    created_at: datetime
