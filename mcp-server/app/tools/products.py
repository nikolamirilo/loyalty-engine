"""Product catalog tools, used for purchase-based loyalty flows (see
`purchase_product` in `app.tools.purchases`). Listing/getting requires the
``read`` scope; creating, updating and deleting a product require ``write``.
"""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core import annotations as ann
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool(title="Products: Create", annotations=ann.WRITE)
async def create_product(
    name: str,
    price_cents: int,
    description: Optional[str] = None,
    currency: str = "EUR",
    category: Optional[str] = None,
    is_active: bool = True,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a purchasable product. `price_cents` is the unit price in the
    smallest unit of `currency` (e.g. cents for EUR/USD).

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
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
    return await api.post("/products", body, program=program)


@mcp.tool(title="Products: List", annotations=ann.READ)
async def list_products(
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    program: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List the product catalog, newest first, optionally restricted to active products.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(
        "/products",
        params={"active_only": active_only, "skip": skip, "limit": limit},
        program=program,
    )


@mcp.tool(title="Products: Get", annotations=ann.READ)
async def get_product(product_id: str, program: Optional[str] = None) -> Dict[str, Any]:
    """Get a single product by id.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(f"/products/{product_id}", program=program)


@mcp.tool(title="Products: Update", annotations=ann.WRITE)
async def update_product(
    product_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    price_cents: Optional[int] = None,
    currency: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Update a product. Only the fields provided are changed.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
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
    return await api.patch(f"/products/{product_id}", body, program=program)


@mcp.tool(title="Products: Delete", annotations=ann.DESTRUCTIVE)
async def delete_product(product_id: str, program: Optional[str] = None) -> None:
    """Delete a product from the catalog.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.delete(f"/products/{product_id}", program=program)
