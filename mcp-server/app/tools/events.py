"""Event tools: define event types and their rules, send a member event, and
read what its rules did. Reading event types and events requires the ``read``
scope; managing event types and rules and sending an event require
``write``, since an event's rules can move points and hand out rewards.
"""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core import annotations as ann
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool(title="List Event Types", annotations=ann.READ)
async def list_event_types(program: Optional[str] = None) -> List[Dict[str, Any]]:
    """List the event types a program accepts, each with its `key` (what
    `track_event` takes as `type`), its attributes, and its rules.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get("/event-types", program=program)


@mcp.tool(title="Get Event Type", annotations=ann.READ)
async def get_event_type(event_type_id: str, program: Optional[str] = None) -> Dict[str, Any]:
    """Get a single event type by id, with its attributes and rules.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(f"/event-types/{event_type_id}", program=program)


@mcp.tool(title="Create Event Type", annotations=ann.WRITE)
async def create_event_type(
    name: str,
    description: Optional[str] = None,
    attributes: Optional[List[Dict[str, Any]]] = None,
    is_active: bool = True,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Define an event type members can trigger, such as "Order placed". Its
    `key` is derived from `name` (here `orderPlaced`), never changes, and is
    what `track_event` takes as `type`.

    `attributes` lists the data the event carries, each like
    `{"label": "Amount", "type": "number"}`. `type` is one of `text`,
    `number`, `boolean`, `date` or `select`; a `select` also needs
    `"options": ["Online", "In store"]`. Each attribute's key is derived from
    its label, like the event's. Rules are added with `create_event_rule`.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    body = {
        "name": name,
        "description": description,
        "isActive": is_active,
        "attributes": attributes or [],
    }
    return await api.post("/event-types", body, program=program)


@mcp.tool(title="Update Event Type", annotations=ann.WRITE)
async def update_event_type(
    event_type_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
    attributes: Optional[List[Dict[str, Any]]] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an event type (ids from `list_event_types`). Only the fields
    provided are changed. The `key` never changes, so integrations keep
    working after a rename.

    `attributes`, when given, replaces the whole list. Include every attribute
    to keep, each with its existing `key` (its type can't change); an item
    without a `key` is added as a new attribute. Leaving one out removes it,
    which the API refuses while a rule still uses it.

    Setting `is_active` to false makes the API reject new events of this type
    until it is turned back on.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    body = {
        "name": name,
        "description": description,
        "isActive": is_active,
        "attributes": attributes,
    }
    return await api.patch(f"/event-types/{event_type_id}", body, program=program)


@mcp.tool(title="Delete Event Type", annotations=ann.DELETE)
async def delete_event_type(event_type_id: str, program: Optional[str] = None) -> None:
    """Delete an event type and all its rules. Events already received stay
    in each member's history. To stop accepting it but keep the rules, use
    `update_event_type` with `is_active=False` instead.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.delete(f"/event-types/{event_type_id}", program=program)


@mcp.tool(title="Create Event Rule", annotations=ann.WRITE)
async def create_event_rule(
    event_type_id: str,
    name: str,
    effects: List[Dict[str, Any]],
    conditions: Optional[List[Dict[str, Any]]] = None,
    limit_per_member: Optional[int] = None,
    is_active: bool = True,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a rule to an event type: when an event of that type arrives and
    every condition holds, each effect runs, in order.

    `conditions` is a list of `{"field", "operator", "value"}` checks, all of
    which must hold (no OR: use two rules). `field` is one of:

    - `event.attributes.<key>` - one of this event type's attributes
    - `member.pointsBalance` - operators `eq`, `neq`, `gt`, `gte`, `lt`, `lte`
    - `member.tier` - `eq` or `neq` a tier id from `list_tiers`
    - `member.segments` - `contains` a segment id from `list_segments`
    - `member.customAttributes.<key>` - a key from `list_member_attributes`

    Text takes `eq`, `neq`, `contains`; select `eq`, `neq`; boolean `eq`;
    date `eq`, `gt`, `lt`; number the number operators above. No conditions
    means the rule runs on every event of the type.

    `effects` (at least one) are objects with a `type`:

    - `{"type": "addPoints", "points": 50}` or `"fromAttribute": "<key>"` of
      a number attribute; `burnPoints` takes the same. The tier multiplier
      applies to `addPoints`.
    - `{"type": "grantReward", "rewardId": "..."}`
    - `{"type": "assignChallenge", "challengeId": "..."}`
    - `{"type": "addChallengeProgress", "challengeId": "...", "amount": 1}`
      or `"fromAttribute"` instead of `amount`
    - `{"type": "addToSegment", "segmentId": "..."}`, `removeFromSegment` the
      same
    - `{"type": "updateMember", "fields": [{"field": "member.customAttributes.<key>", "value": ...}]}`;
      `field` may also be `member.name` or `member.phone`, and each item may
      take `"fromAttribute"` instead of `value`

    `limit_per_member` caps how many times the rule can run for one member;
    omit it for no limit.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    body = {
        "name": name,
        "isActive": is_active,
        "conditions": conditions or [],
        "effects": effects,
        "limitPerMember": limit_per_member,
    }
    return await api.post(f"/event-types/{event_type_id}/rules", body, program=program)


@mcp.tool(title="Update Event Rule", annotations=ann.WRITE)
async def update_event_rule(
    event_type_id: str,
    rule_id: str,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    conditions: Optional[List[Dict[str, Any]]] = None,
    effects: Optional[List[Dict[str, Any]]] = None,
    limit_per_member: Optional[int] = None,
    remove_limit: bool = False,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an event rule (ids from `get_event_type`). Only the fields
    provided are changed; `conditions` and `effects`, when given, replace
    the whole list, in the same format as `create_event_rule`. Pass
    `remove_limit=True` (and no `limit_per_member`) to let the rule run any
    number of times per member.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    if remove_limit and limit_per_member is not None:
        raise ValueError("Pass either `limit_per_member` or `remove_limit`, not both.")
    body = {
        "name": name,
        "isActive": is_active,
        "conditions": conditions,
        "effects": effects,
        "limitPerMember": limit_per_member,
    }
    clear = ("limitPerMember",) if remove_limit else ()
    return await api.patch(
        f"/event-types/{event_type_id}/rules/{rule_id}", body, program=program, clear=clear
    )


@mcp.tool(title="Delete Event Rule", annotations=ann.DELETE)
async def delete_event_rule(
    event_type_id: str, rule_id: str, program: Optional[str] = None
) -> None:
    """Delete an event rule. What it already did to members stays. To pause
    it instead, use `update_event_rule` with `is_active=False`.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.delete(f"/event-types/{event_type_id}/rules/{rule_id}", program=program)


@mcp.tool(title="Track Event", annotations=ann.WRITE)
async def track_event(
    member_id: str,
    type: str,
    attributes: Optional[Dict[str, Any]] = None,
    event_id: Optional[str] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Record an event for a member and run its rules. `type` is an event type
    key from `list_event_types`, and `attributes` holds that type's attribute
    values. The result's `effects` lists what each matching rule did, such as
    points added or a reward given.

    Pass `event_id` (your own id for the event) to make retries safe: the same
    id again returns the first result and runs nothing.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(
        "/events",
        {"memberId": member_id, "type": type, "attributes": attributes or {}, "eventId": event_id},
        program=program,
    )


@mcp.tool(title="List Member Events", annotations=ann.READ)
async def list_member_events(
    member_id: str, skip: int = 0, limit: int = 50, program: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List the events received for a member, newest first, each with the
    effects its rules applied.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(
        f"/members/{member_id}/events",
        params={"skip": skip, "limit": limit},
        program=program,
    )


@mcp.tool(title="List Events", annotations=ann.READ)
async def list_events(
    type: Optional[str] = None, skip: int = 0, limit: int = 50, program: Optional[str] = None
) -> List[Dict[str, Any]]:
    """The program's event log: every event received, newest first, with the
    member it was for and the effects its rules applied. `type` narrows it to
    one event type key.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(
        "/events", params={"type": type, "skip": skip, "limit": limit}, program=program
    )
