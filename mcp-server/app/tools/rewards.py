"""Reward catalog tools. Listing/getting requires the ``read`` scope;
creating, updating and deleting a reward require ``write``.
"""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core import annotations as ann
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool(title="List Rewards", annotations=ann.READ)
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
        params={"active_only": active_only, "skip": skip, "limit": limit},
        program=program,
    )


@mcp.tool(title="Get Reward", annotations=ann.READ)
async def get_reward(reward_id: str, program: Optional[str] = None) -> Dict[str, Any]:
    """Get a single reward by id.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(f"/rewards/{reward_id}", program=program)


@mcp.tool(title="Create Reward", annotations=ann.WRITE)
async def create_reward(
    name: str,
    points_cost: int,
    description: Optional[str] = None,
    stock: Optional[int] = None,
    is_active: bool = True,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a reward members can redeem for `points_cost` points. `stock` is
    how many can be redeemed in total; omit it for unlimited.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    body = {
        "name": name,
        "description": description,
        "points_cost": points_cost,
        "stock": stock,
        "is_active": is_active,
    }
    return await api.post("/rewards", body, program=program)


@mcp.tool(title="Update Reward", annotations=ann.WRITE)
async def update_reward(
    reward_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    points_cost: Optional[int] = None,
    stock: Optional[int] = None,
    unlimited_stock: bool = False,
    is_active: Optional[bool] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Update a reward. Only the fields provided are changed. Pass
    `unlimited_stock=True` (and no `stock`) to remove its stock limit;
    `is_active=False` hides it from redemption without deleting it.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    if unlimited_stock and stock is not None:
        raise ValueError("Pass either `stock` or `unlimited_stock`, not both.")
    body = {
        "name": name,
        "description": description,
        "points_cost": points_cost,
        "stock": stock,
        "is_active": is_active,
    }
    clear = ("stock",) if unlimited_stock else ()
    return await api.patch(f"/rewards/{reward_id}", body, program=program, clear=clear)


@mcp.tool(title="Delete Reward", annotations=ann.DELETE)
async def delete_reward(reward_id: str, program: Optional[str] = None) -> None:
    """Delete a reward from the catalog. To stop redemptions but keep it,
    use `update_reward` with `is_active=False` instead.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.delete(f"/rewards/{reward_id}", program=program)
