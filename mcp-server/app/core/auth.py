"""Bearer-token authentication and per-tool scope checks.

Two distinct bearer tokens exist in this service:
  - the *inbound* one, resolved here into a ``ClientPrincipal``, identifying
    which external agent is calling this MCP server and what it's allowed
    to do;
  - the *outbound* one (``settings.loyalty_api_service_token``, used by
    ``app.client.loyalty_api_client``), sent on every call this server makes
    to the loyalty API, regardless of which external caller triggered it.

Keeping them separate means a compromised or misbehaving external client can
be revoked by editing ``MCP_CLIENT_TOKENS`` without touching the loyalty
API's own credential.
"""

import contextvars
from typing import Optional

from app.core.config import ClientPrincipal, settings

# Set by BearerAuthMiddleware for the duration of one HTTP request, read by
# require_scope() inside whichever tool function that request invokes.
_current_principal: contextvars.ContextVar[Optional[ClientPrincipal]] = contextvars.ContextVar(
    "current_principal", default=None
)


class NotAuthorized(Exception):
    """Raised when the caller authenticated for this request lacks the scope
    a tool requires. FastMCP turns this into a normal tool error result."""


def authenticate(token: Optional[str]) -> Optional[ClientPrincipal]:
    if not token:
        return None
    return settings.client_tokens.get(token)


def set_current_principal(principal: Optional[ClientPrincipal]) -> contextvars.Token:
    return _current_principal.set(principal)


def reset_current_principal(reset_token: contextvars.Token) -> None:
    _current_principal.reset(reset_token)


def require_scope(scope: str) -> ClientPrincipal:
    """Call at the top of every tool. "admin" satisfies any scope check."""
    principal = _current_principal.get()
    if principal is None:
        raise NotAuthorized("Not authenticated")
    if scope not in principal.scopes and "admin" not in principal.scopes:
        raise NotAuthorized(f"'{principal.name}' is not authorized for the '{scope}' scope")
    return principal
