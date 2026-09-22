"""Double opt-in email verification tools. Both trigger and verify require
the ``write`` scope - there's no meaningful read-only DOI operation.

Neither declares ``annotations``, and that is deliberate. These are the only
two tools that reach an address outside the system, so they deserve a
permission decision of their own, separate from the writes that stay inside
the loyalty API. A client has no field to express that - see "How tools are
grouped" in the README - but Claude does put every unannotated tool in its
own **Other tools** section, with its own allow/ask toggle. Leaving these two
unannotated is what buys that section. Nothing else here should follow suit.
"""

from typing import Any, Dict, Optional

from app.client import loyalty_api_client as api
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool(title="Send Email Verification")
async def trigger_doi(
    email: Optional[str] = None,
    member_id: Optional[str] = None,
    type: str = "code",
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a double opt-in verification email to a member, identified by
    `email` or `member_id` (exactly one is required). `type` is "code" (a
    6-digit code the member types back in) or "link" (a verify-my-email
    button); defaults to "code".

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(
        "/doi/trigger",
        {"email": email, "member_id": member_id, "type": type},
        program=program,
    )


@mcp.tool(title="Confirm Email Verification")
async def verify_doi(
    code: str,
    email: Optional[str] = None,
    member_id: Optional[str] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Confirm a DOI verification code for a member, identified by `email` or
    `member_id` (exactly one is required).

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(
        "/doi/verify",
        {"email": email, "member_id": member_id, "code": code},
        program=program,
    )
