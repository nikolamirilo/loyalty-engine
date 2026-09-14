"""Product catalog tools, used for purchase-based loyalty flows (see
`purchase_product` in `app.tools.purchases`). Listing/getting requires the
``read`` scope; creating, updating and deleting a product require ``write``.
"""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool(title="Products: Create")
async def create_product(
    name: str,
    price_cents: int,
    description: Optional[str] = None,
    currency: str = "EUR",
    category: Optional[str] = None,
    is_active: bool = True,
) -> Dict[str, Any]:
    """Create a purchasable product. `price_cents` is the unit price in the
    smallest unit of `currency` (e.g. cents for EUR/USD).
    """
    require_scope("write")
    body = {
        "name": name,
        "description": description,
        "price_cents": price_cents,
        "currency": currency,
        "category": category,
        "is_active": is_active,
    }
    return await api.post("/products", body)


@mcp.tool(title="Products: List")
async def list_products(
    active_only: bool = False, skip: int = 0, limit: int = 100
) -> List[Dict[str, Any]]:
    """List the product catalog, newest first, optionally restricted to active products."""
    require_scope("read")
    return await api.get(
        "/products", params={"activeOnly": active_only, "skip": skip, "limit": limit}
    )


@mcp.tool(title="Products: Get")
async def get_product(product_id: str) -> Dict[str, Any]:
    """Get a single product by id."""
    require_scope("read")
    return await api.get(f"/products/{product_id}")


@mcp.tool(title="Products: Update")
async def update_product(
    product_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    price_cents: Optional[int] = None,
    currency: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update a product. Only the fields provided are changed."""
    require_scope("write")
    body = {
        "name": name,
        "description": description,
        "price_cents": price_cents,
        "currency": currency,
        "category": category,
        "is_active": is_active,
    }
    return await api.patch(f"/products/{product_id}", body)


@mcp.tool(title="Products: Delete")
async def delete_product(product_id: str) -> None:
    """Delete a product from the catalog."""
    require_scope("write")
    return await api.delete(f"/products/{product_id}")
