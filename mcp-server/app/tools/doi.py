"""Double opt-in email verification tools. Both trigger and verify require
the ``write`` scope - there's no meaningful read-only DOI operation.
"""

from typing import Any, Dict, Optional

from app.client import loyalty_api_client as api
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool()
async def trigger_doi(
    email: Optional[str] = None,
    member_id: Optional[str] = None,
    type: str = "code",
) -> Dict[str, Any]:
    """Send a double opt-in verification email to a member, identified by
    `email` or `member_id` (exactly one is required). `type` is "code" (a
    6-digit code the member types back in) or "link" (a verify-my-email
    button); defaults to "code".
    """
    require_scope("write")
    return await api.post(
        "/doi/trigger", {"email": email, "member_id": member_id, "type": type}
    )


@mcp.tool()
async def verify_doi(
    code: str, email: Optional[str] = None, member_id: Optional[str] = None
) -> Dict[str, Any]:
    """Confirm a DOI verification code for a member, identified by `email` or
    `member_id` (exactly one is required).
    """
    require_scope("write")
    return await api.post(
        "/doi/verify", {"email": email, "member_id": member_id, "code": code}
    )
