"""Reward redemption tools, plus admin-granted prizes: rewards handed to a
member at no points cost (e.g. as a challenge completion reward, or a manual
goodwill grant). Both share the same `Redemption` record, distinguished by
`source` (`redeemed` vs `assigned`).
"""

from typing import Any, Dict, List, Optional

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


@mcp.tool()
async def assign_prize(member_id: str, reward_id: str) -> Dict[str, Any]:
    """Grant a reward to a member at no points cost (source "assigned"), e.g.
    as a goodwill gesture or a manual campaign prize. Still subject to the
    reward's own availability (active, in stock) - just skips the balance
    check and debit that `redeem_reward` performs.
    """
    require_scope("write")
    return await api.post(f"/members/{member_id}/prizes/{reward_id}")


@mcp.tool()
async def list_member_prizes(
    member_id: str, source: Optional[str] = None, skip: int = 0, limit: int = 50
) -> List[Dict[str, Any]]:
    """List a member's prize/redemption history, newest first. `source`
    optionally filters to "redeemed" (member spent points) or "assigned"
    (granted at no cost, e.g. via `assign_prize` or a completed challenge).
    """
    require_scope("read")
    return await api.get(
        f"/members/{member_id}/prizes",
        params={"source": source, "skip": skip, "limit": limit},
    )
