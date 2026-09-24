"""Event tools: define event types, send a member event, and read what its
rules did. Listing event types and a member's events requires the ``read``
scope; creating or updating an event type and sending an event require
``write``, since an event's rules can move points and hand out rewards.

Rules themselves are still managed in the admin console (and the
`/event-types/{id}/rules` API).
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
    its label, like the event's. Rules are added in the admin console.

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
