"""Entry point: wires the FastMCP app behind bearer-token auth and exposes
the ASGI app uvicorn serves.

Run locally the same way the loyalty API itself is run:

    uvicorn app.server:app --reload --port 8100

Tools live in ``app/tools/``, one module per resource, imported below purely
for the side effect of registering onto ``app.mcp_instance.mcp``.
"""

from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from app import tools  # noqa: F401 - registers every @mcp.tool()
from app.core.config import settings
from app.core.landing import PUBLIC_ROUTES
from app.core.middleware import BearerAuthMiddleware
from app.mcp_instance import mcp


async def healthz(request):
    return JSONResponse({"status": "ok"})


# stateless_http=True because each request may land on a different serverless
# instance: the stateful mode keeps sessions in a per-process dict, so a
# follow-up request carrying an Mcp-Session-Id created elsewhere gets a 404.
# transport_security must be passed explicitly: left unset, the SDK sees the
# default host of 127.0.0.1 and locks Host/Origin to localhost, which rejects
# the deployed domain with a 421.
app = mcp.streamable_http_app(
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        allowed_hosts=settings.allowed_hosts,
        allowed_origins=settings.allowed_origins,
    ),
)
app.routes.append(Route("/healthz", healthz, methods=["GET"]))
app.routes.extend(PUBLIC_ROUTES)
app.add_middleware(BearerAuthMiddleware)
# Added last so it wraps BearerAuthMiddleware, letting Starlette answer the
# browser's OPTIONS preflight (sent by claude.ai before its Authorization
# POST) without that request first hitting the 401 auth check.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://claude.ai"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["authorization", "content-type", "mcp-protocol-version"],
)
