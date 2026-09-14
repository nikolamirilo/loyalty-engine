"""Segment tools. Read-only for now - creating/editing/deleting segments and
assigning members to them are program-configuration actions, held back for a
future admin scope rather than exposed here.
"""

from typing import Any, Dict, List

from app.client import loyalty_api_client as api
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool(title="Segments: List")
async def list_segments() -> List[Dict[str, Any]]:
    """List all member segments (e.g. "VIP", "Newsletter") with member counts."""
    require_scope("read")
    return await api.get("/segments")


@mcp.tool(title="Segments: Get")
async def get_segment(segment_id: str) -> Dict[str, Any]:
    """Get a single segment by id."""
    require_scope("read")
    return await api.get(f"/segments/{segment_id}")
