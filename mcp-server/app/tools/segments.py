"""Segment tools. Read-only for now - creating/editing/deleting segments and
assigning members to them are program-configuration actions, held back for a
future admin scope rather than exposed here.
"""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core import annotations as ann
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool(title="Segments: List", annotations=ann.READ)
async def list_segments(program: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all member segments (e.g. "VIP", "Newsletter") with member counts.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get("/segments", program=program)


@mcp.tool(title="Segments: Get", annotations=ann.READ)
async def get_segment(segment_id: str, program: Optional[str] = None) -> Dict[str, Any]:
    """Get a single segment by id.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(f"/segments/{segment_id}", program=program)
