"""Member tools. Listing/getting requires the ``read`` scope; creating and
updating a member requires ``write``. Deleting a member is an admin action
and isn't exposed by this server yet.
"""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core import annotations as ann
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool(title="Members: List", annotations=ann.READ)
async def list_members(
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    program: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List loyalty program members, optionally filtered by a name/email substring.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(
        "/members", params={"q": q, "skip": skip, "limit": limit}, program=program
    )


@mcp.tool(title="Members: Get", annotations=ann.READ)
async def get_member(member_id: str, program: Optional[str] = None) -> Dict[str, Any]:
    """Get a single member by id, including their segments and points balance.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(f"/members/{member_id}", program=program)


@mcp.tool(title="Members: Create", annotations=ann.WRITE)
async def create_member(
    name: str,
    email: str,
    phone: Optional[str] = None,
    segment_ids: Optional[List[str]] = None,
    custom_attributes: Optional[Dict[str, Any]] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new member. `segment_ids` must reference existing segments
    (see `list_segments`); omit to create the member unassigned.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    body = {
        "name": name,
        "email": email,
        "phone": phone,
        "segment_ids": segment_ids or [],
        "custom_attributes": custom_attributes or {},
    }
    return await api.post("/members", body, program=program)


@mcp.tool(title="Members: Update", annotations=ann.WRITE)
async def update_member(
    member_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    segment_ids: Optional[List[str]] = None,
    custom_attributes: Optional[Dict[str, Any]] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Update a member. Only the fields provided are changed. `custom_attributes`
    is merged into the member's existing attributes (one level deep) rather than
    replacing them; a key set to null clears just that value.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    body = {
        "name": name,
        "email": email,
        "phone": phone,
        "segment_ids": segment_ids,
        "custom_attributes": custom_attributes,
    }
    return await api.patch(f"/members/{member_id}", body, program=program)
