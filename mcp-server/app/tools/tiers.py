"""Tier tools. Read-only for now - creating/editing/deleting tiers is a
program-configuration action, held back for a future admin scope rather than
exposed here.
"""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool()
async def list_tiers(program: Optional[str] = None) -> List[Dict[str, Any]]:
    """List point-threshold tiers in ascending order of `minPoints`.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get("/tiers", program=program)


@mcp.tool()
async def get_tier(tier_id: str, program: Optional[str] = None) -> Dict[str, Any]:
    """Get a single tier by id.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(f"/tiers/{tier_id}", program=program)
