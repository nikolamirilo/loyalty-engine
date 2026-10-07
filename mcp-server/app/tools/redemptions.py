"""Reward redemption tools, plus admin-granted prizes: rewards handed to a
member at no points cost (e.g. as a challenge completion reward, or a manual
goodwill grant). Both share the same `Redemption` record, distinguished by
`source` (`redeemed` vs `assigned`).
"""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core import annotations as ann
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool(title="Redeem Reward", annotations=ann.WRITE)
async def redeem_reward(
    member_id: str, reward_id: str, program: Optional[str] = None
) -> Dict[str, Any]:
    """Redeem a reward for a member, debiting its points cost from their balance.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(f"/members/{member_id}/redeem/{reward_id}", program=program)


@mcp.tool(title="List Member Redemptions", annotations=ann.READ)
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


@mcp.tool(title="Grant Prize", annotations=ann.WRITE)
async def assign_prize(
    member_id: str,
    reward_id: str,
    send_email: bool = False,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Grant a reward to a member at no points cost (source "assigned"), e.g.
    as a goodwill gesture or a manual campaign prize. Still subject to the
    reward's own availability (active, in stock) - just skips the balance
    check and debit that `redeem_reward` performs.

    `send_email` also emails the member about the prize, with a button that
    opens the member app's claim page for it. The prize is assigned even if
    the email fails; `emailSent` and `emailError` in the result say how it went.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(
        f"/members/{member_id}/prizes/{reward_id}",
        {"sendEmail": send_email},
        program=program,
    )


@mcp.tool(title="Claim Prize", annotations=ann.WRITE)
async def claim_prize(
    member_id: str, redemption_id: str, program: Optional[str] = None
) -> Dict[str, Any]:
    """Mark a member's assigned prize as claimed (sets `claimedAt`), the same
    as the member pressing "Claim" in their wallet. `redemption_id` is the
    prize's id from `list_member_prizes`. Claiming twice changes nothing.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(
        f"/members/{member_id}/prizes/{redemption_id}/claim", program=program
    )


@mcp.tool(title="List Member Prizes", annotations=ann.READ)
async def list_member_prizes(
    member_id: str,
    source: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    program: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List a member's prize/redemption history, newest first. `source`
    optionally filters to "redeemed" (member spent points) or "assigned"
    (granted at no cost, e.g. via `assign_prize` or a completed challenge).
    An assigned prize's `claimedAt` is null until the member claims it.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(
        f"/members/{member_id}/prizes",
        params={"source": source, "skip": skip, "limit": limit},
        program=program,
    )
