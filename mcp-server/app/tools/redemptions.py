"""Reward redemption tools."""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool()
async def redeem_reward(
    member_id: str, reward_id: str, program: Optional[str] = None
) -> Dict[str, Any]:
    """Redeem a reward for a member, debiting its points cost from their balance.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(f"/members/{member_id}/redeem/{reward_id}", program=program)


@mcp.tool()
async def list_member_redemptions(
    member_id: str, skip: int = 0, limit: int = 50, program: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List a member's redemption history, newest first.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(
        f"/members/{member_id}/redemptions",
        params={"skip": skip, "limit": limit},
        program=program,
    )
