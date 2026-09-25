"""Custom member attribute definitions - the program-specific fields (e.g.
"Favourite store") every member carries in `customAttributes`. Listing/getting
requires the ``read`` scope; creating, updating and deleting a definition
require ``write``.

Setting a member's value for one goes through `update_member`'s
`custom_attributes`, keyed by the definition's `key`.
"""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core import annotations as ann
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool(title="List Member Attributes", annotations=ann.READ)
async def list_member_attributes(program: Optional[str] = None) -> List[Dict[str, Any]]:
    """List the custom attribute definitions, each with its `key` (what
    `custom_attributes` and `member.customAttributes.<key>` conditions use),
    `label`, `type`, `options` and `defaultValue`.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get("/member-attributes", program=program)


@mcp.tool(title="Get Member Attribute", annotations=ann.READ)
async def get_member_attribute(attribute_id: str, program: Optional[str] = None) -> Dict[str, Any]:
    """Get a single custom attribute definition by id.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(f"/member-attributes/{attribute_id}", program=program)


@mcp.tool(title="Create Member Attribute", annotations=ann.WRITE)
async def create_member_attribute(
    label: str,
    type: str,
    options: Optional[List[str]] = None,
    default_value: Optional[Any] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Define a custom attribute every member in the program carries. `type`
    is one of `text`, `number`, `boolean`, `date` or `select`; a `select`
    also needs `options`. The `key` is derived from `label` and never changes.

    A `default_value` is written onto every existing member straight away,
    and onto each member created later.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    body = {"label": label, "type": type, "options": options, "default_value": default_value}
    return await api.post("/member-attributes", body, program=program)


@mcp.tool(title="Update Member Attribute", annotations=ann.WRITE)
async def update_member_attribute(
    attribute_id: str,
    label: Optional[str] = None,
    options: Optional[List[str]] = None,
    default_value: Optional[Any] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Update a custom attribute definition. Only the fields provided are
    changed; `key` and `type` are fixed once created. A new `default_value`
    applies to members created from now on and leaves existing values alone.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    body = {"label": label, "options": options, "default_value": default_value}
    return await api.patch(f"/member-attributes/{attribute_id}", body, program=program)


@mcp.tool(title="Delete Member Attribute", annotations=ann.DELETE)
async def delete_member_attribute(attribute_id: str, program: Optional[str] = None) -> None:
    """Delete a custom attribute definition and erase its value from every
    member in the program.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.delete(f"/member-attributes/{attribute_id}", program=program)
