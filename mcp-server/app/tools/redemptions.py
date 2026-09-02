"""Reward redemption tools."""

from typing import Any, Dict, List

from app.client import loyalty_api_client as api
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool()
async def redeem_reward(member_id: str, reward_id: str) -> Dict[str, Any]:
    """Redeem a reward for a member, debiting its points cost from their balance."""
    require_scope("write")
    return await api.post(f"/members/{member_id}/redeem/{reward_id}")


@mcp.tool()
async def list_member_redemptions(
    member_id: str, skip: int = 0, limit: int = 50
) -> List[Dict[str, Any]]:
    """List a member's redemption history, newest first."""
    require_scope("read")
    return await api.get(
        f"/members/{member_id}/redemptions", params={"skip": skip, "limit": limit}
    )
