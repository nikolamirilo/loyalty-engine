"""Reward catalog tools. Read-only for now - creating/editing/deleting
rewards is a program-configuration action, held back for a future admin
scope rather than exposed here.
"""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool()
async def list_rewards(
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    program: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List the reward catalog, optionally restricted to active rewards.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(
        "/rewards",
        params={"activeOnly": active_only, "skip": skip, "limit": limit},
        program=program,
    )


@mcp.tool()
async def get_reward(reward_id: str, program: Optional[str] = None) -> Dict[str, Any]:
    """Get a single reward by id.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(f"/rewards/{reward_id}", program=program)
