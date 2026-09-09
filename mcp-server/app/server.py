"""Entry point: wires the FastMCP app behind bearer-token auth and exposes
the ASGI app uvicorn serves.

Run locally the same way the loyalty API itself is run:

    uvicorn app.server:app --reload --port 8100

Tools live in ``app/tools/``, one module per resource, imported below purely
for the side effect of registering onto ``app.mcp_instance.mcp``.
"""

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from app import tools  # noqa: F401 - registers every @mcp.tool()
from app.core.middleware import BearerAuthMiddleware
from app.mcp_instance import mcp


async def healthz(request):
    return JSONResponse({"status": "ok"})


app = mcp.streamable_http_app()
app.routes.append(Route("/healthz", healthz, methods=["GET"]))
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
