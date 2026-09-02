"""ASGI middleware that authenticates every HTTP request to the MCP server.

Implemented as a plain ASGI middleware (``__call__(scope, receive, send)``),
not Starlette's ``BaseHTTPMiddleware``: the latter runs the downstream app in
a separate task in some Starlette versions, which would make a contextvar
set here invisible by the time a tool call reads it further down the stack.
A plain ASGI middleware runs in the same task as everything it wraps, so the
principal set below is reliably visible to ``require_scope()``.
"""

import json

from app.core.auth import authenticate, reset_current_principal, set_current_principal

# Unauthenticated paths for infra health checks (Vercel, uptime monitors).
# The MCP protocol endpoints themselves always require a valid bearer token.
_UNAUTHENTICATED_PATHS = {"/healthz"}


class BearerAuthMiddleware:
    def __init__(self, app):
        self._app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] in _UNAUTHENTICATED_PATHS:
            await self._app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        raw_auth = headers.get(b"authorization", b"").decode("latin-1")
        token = raw_auth[len("Bearer "):].strip() if raw_auth.startswith("Bearer ") else None
        principal = authenticate(token)

        if principal is None:
            body = json.dumps(
                {"error": "invalid_token", "message": "Missing or invalid bearer token"}
            ).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"www-authenticate", b"Bearer"),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return

        reset_token = set_current_principal(principal)
        try:
            await self._app(scope, receive, send)
        finally:
            reset_current_principal(reset_token)
