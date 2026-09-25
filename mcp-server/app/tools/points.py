"""Points balance/transaction tools. Earning, burning and adjusting points
require the ``write`` scope.
"""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core import annotations as ann
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool(title="Get Points Balance", annotations=ann.READ)
async def get_member_balance(
    member_id: str, program: Optional[str] = None
) -> Dict[str, Any]:
    """Get a member's current points balance.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(f"/members/{member_id}/balance", program=program)


@mcp.tool(title="List Point Transactions", annotations=ann.READ)
async def list_transactions(
    member_id: str, skip: int = 0, limit: int = 50, program: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List a member's points transaction history, newest first.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(
        f"/members/{member_id}/transactions",
        params={"skip": skip, "limit": limit},
        program=program,
    )


@mcp.tool(title="Earn Points", annotations=ann.WRITE)
async def earn_points(
    member_id: str,
    points: int,
    description: Optional[str] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Award points to a member. The member's tier multiplier (if any) is
    applied automatically, so the amount credited may exceed `points`.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(
        f"/members/{member_id}/points/earn",
        {"points": points, "description": description},
        program=program,
    )


@mcp.tool(title="Burn Points", annotations=ann.WRITE)
async def burn_points(
    member_id: str,
    points: int,
    description: Optional[str] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Spend points from a member's balance. Fails if the balance is insufficient.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(
        f"/members/{member_id}/points/burn",
        {"points": points, "description": description},
        program=program,
    )


@mcp.tool(title="Adjust Points", annotations=ann.WRITE)
async def adjust_points(
    member_id: str,
    points: int,
    description: Optional[str] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Correct a member's balance by `points`, positive or negative, recorded
    as an `adjust` transaction. Unlike `earn_points`, no tier multiplier is
    applied. Fails if the balance would go below zero.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(
        f"/members/{member_id}/points/adjust",
        {"points": points, "description": description},
        program=program,
    )
