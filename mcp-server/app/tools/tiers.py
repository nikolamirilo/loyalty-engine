"""Tier tools. Read-only for now - creating/editing/deleting tiers is a
program-configuration action, held back for a future admin scope rather than
exposed here.
"""

from typing import Any, Dict, List

from app.client import loyalty_api_client as api
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool()
async def list_tiers() -> List[Dict[str, Any]]:
    """List point-threshold tiers in ascending order of `minPoints`."""
    require_scope("read")
    return await api.get("/tiers")


@mcp.tool()
async def get_tier(tier_id: str) -> Dict[str, Any]:
    """Get a single tier by id."""
    require_scope("read")
    return await api.get(f"/tiers/{tier_id}")
