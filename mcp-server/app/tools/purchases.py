"""Purchase tools. Members "buy" catalog products on unlimited credit - no
balance is checked and nothing is debited from their points; purchases exist
purely as a spend signal for gamification (e.g. challenge progress, segment
targeting). Listing/getting requires the ``read`` scope; recording a purchase
requires ``write``.
"""

from typing import Any, Dict, List

from app.client import loyalty_api_client as api
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool()
async def purchase_product(member_id: str, product_id: str, quantity: int = 1) -> Dict[str, Any]:
    """Record a member purchasing a product. Fails if the product doesn't
    exist or isn't currently purchasable (inactive).
    """
    require_scope("write")
    return await api.post(
        f"/members/{member_id}/purchases", {"product_id": product_id, "quantity": quantity}
    )


@mcp.tool()
async def list_member_purchases(
    member_id: str, skip: int = 0, limit: int = 50
) -> List[Dict[str, Any]]:
    """List a member's purchase history, newest first."""
    require_scope("read")
    return await api.get(
        f"/members/{member_id}/purchases", params={"skip": skip, "limit": limit}
    )


@mcp.tool()
async def get_member_purchase_stats(member_id: str, days: int = 7) -> Dict[str, Any]:
    """Get a member's purchase/spend stats: lifetime totals plus a trailing
    `days`-day window (purchase count, total spend, average order value,
    days since last purchase, ...).
    """
    require_scope("read")
    return await api.get(f"/members/{member_id}/purchase-stats", params={"days": days})
