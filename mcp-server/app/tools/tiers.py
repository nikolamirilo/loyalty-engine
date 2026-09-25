"""Tier tools. Listing/getting requires the ``read`` scope; creating,
updating and deleting a tier require ``write``.

Every tier write makes the API re-check which tier each member of the program
qualifies for, so one call can promote or demote many members at once.
"""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core import annotations as ann
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool(title="List Tiers", annotations=ann.READ)
async def list_tiers(program: Optional[str] = None) -> List[Dict[str, Any]]:
    """List tiers in ascending order of `rank`, each with the conditions
    (points balance, purchase spend/count, segments, custom attributes) a
    member must meet to hold it.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get("/tiers", program=program)


@mcp.tool(title="Get Tier", annotations=ann.READ)
async def get_tier(tier_id: str, program: Optional[str] = None) -> Dict[str, Any]:
    """Get a single tier by id.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(f"/tiers/{tier_id}", program=program)


@mcp.tool(title="Create Tier", annotations=ann.WRITE)
async def create_tier(
    name: str,
    rank: int = 0,
    conditions: Optional[List[Dict[str, Any]]] = None,
    multiplier: float = 1.0,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a tier. Members hold the highest-`rank` tier whose conditions
    they all meet. `multiplier` (> 0) scales the points they earn.

    `conditions` is a list of `{"field", "operator", "value"}` checks, all of
    which must hold (no OR: use two tiers). `field` is one of:

    - `member.pointsBalance`, `member.purchaseSpendCents`,
      `member.purchaseCount` - numbers; operators `eq`, `neq`, `gt`, `gte`,
      `lt`, `lte`
    - `member.segments` - operator `contains`, value a segment id from
      `list_segments`
    - `member.customAttributes.<key>` - a key from `list_member_attributes`;
      text takes `eq`, `neq`, `contains`, select `eq`, `neq`, boolean `eq`,
      date `eq`, `gt`, `lt`, number the number operators

    No conditions means every member qualifies, the usual shape of a
    lowest-rank default tier.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    body = {
        "name": name,
        "rank": rank,
        "conditions": conditions or [],
        "multiplier": multiplier,
    }
    return await api.post("/tiers", body, program=program)


@mcp.tool(title="Update Tier", annotations=ann.WRITE)
async def update_tier(
    tier_id: str,
    name: Optional[str] = None,
    rank: Optional[int] = None,
    conditions: Optional[List[Dict[str, Any]]] = None,
    multiplier: Optional[float] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Update a tier. Only the fields provided are changed; `conditions`,
    when given, replaces the whole list (pass `[]` to drop them all), in the
    same format as `create_tier`.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    body = {
        "name": name,
        "rank": rank,
        "conditions": conditions,
        "multiplier": multiplier,
    }
    return await api.patch(f"/tiers/{tier_id}", body, program=program)


@mcp.tool(title="Delete Tier", annotations=ann.DELETE)
async def delete_tier(tier_id: str, program: Optional[str] = None) -> None:
    """Delete a tier. Its members move to the next tier they qualify for, or
    to none.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.delete(f"/tiers/{tier_id}", program=program)
