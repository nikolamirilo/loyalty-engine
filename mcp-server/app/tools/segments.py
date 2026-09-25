"""Segment tools. Listing/getting requires the ``read`` scope; creating,
updating, deleting a segment and assigning members to it require ``write``.

Removing one member from a segment goes through `update_member`, whose
`segment_ids` is that member's full segment list.
"""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core import annotations as ann
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool(title="List Segments", annotations=ann.READ)
async def list_segments(program: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all member segments (e.g. "VIP", "Newsletter") with member counts.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get("/segments", program=program)


@mcp.tool(title="Get Segment", annotations=ann.READ)
async def get_segment(segment_id: str, program: Optional[str] = None) -> Dict[str, Any]:
    """Get a single segment by id.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(f"/segments/{segment_id}", program=program)


@mcp.tool(title="Create Segment", annotations=ann.WRITE)
async def create_segment(
    name: str,
    description: Optional[str] = None,
    color: Optional[str] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a member segment, such as "VIP". `color` is a hex accent for
    its badge in the admin console, e.g. `#22c55e`.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    body = {"name": name, "description": description, "color": color}
    return await api.post("/segments", body, program=program)


@mcp.tool(title="Update Segment", annotations=ann.WRITE)
async def update_segment(
    segment_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    color: Optional[str] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Update a segment. Only the fields provided are changed.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    body = {"name": name, "description": description, "color": color}
    return await api.patch(f"/segments/{segment_id}", body, program=program)


@mcp.tool(title="Delete Segment", annotations=ann.DELETE)
async def delete_segment(segment_id: str, program: Optional[str] = None) -> None:
    """Delete a segment. Its members lose it, and it is removed from any
    challenge it was bulk-assigned to.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.delete(f"/segments/{segment_id}", program=program)


@mcp.tool(title="Assign Members to Segment", annotations=ann.WRITE)
async def assign_members_to_segment(
    segment_id: str, member_ids: List[str], program: Optional[str] = None
) -> Dict[str, Any]:
    """Add members to a segment. Members already in it are skipped, and each
    newly added one also gets the challenges bulk-assigned to the segment.
    Returns `assigned` and `skipped` counts.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(
        f"/segments/{segment_id}/assign", {"member_ids": member_ids}, program=program
    )
