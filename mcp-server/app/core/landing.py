"""The public pages at the server's origin: a landing page at ``/`` and the logo
at the paths browsers and favicon crawlers look for.

Without these, every path except ``/healthz`` answered 401, so anything deriving
an icon from the origin got an auth error instead of the logo. No Claude client
reads the origin today - claude.ai looks the tile up in Google's favicon service
by domain, see mcp-server/README.md - so this is for browsers, crawlers and
whichever client starts reading the host first.
"""

from html import escape

from starlette.responses import HTMLResponse, Response
from starlette.routing import Route

from app.core.branding import asset_bytes
from app.core.config import settings

_ICON_CACHE_CONTROL = "public, max-age=86400"


def _asset_endpoint(filename: str, media_type: str):
    body = asset_bytes(filename)

    async def endpoint(request):
        return Response(body, media_type=media_type, headers={"cache-control": _ICON_CACHE_CONTROL})

    return endpoint


_NAME = escape(settings.project_name)

_LANDING_HTML = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_NAME}</title>
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="/icon.png" type="image/png" sizes="192x192">
  <link rel="apple-touch-icon" href="/icon.png">
  <style>
    body {{ margin: 0; min-height: 100vh; display: grid; place-items: center;
           font-family: system-ui, sans-serif; background: #f6f5fb; color: #1f1b3a; }}
    main {{ text-align: center; }}
    img {{ width: 96px; height: 96px; }}
    h1 {{ font-size: 1.25rem; margin: 1rem 0 0.25rem; }}
    p {{ margin: 0; color: #5b5873; }}
    code {{ background: #ecebf5; padding: 0.1rem 0.35rem; border-radius: 4px; }}
  </style>
</head>
<body>
  <main>
    <img src="/favicon.svg" alt="">
    <h1>{_NAME}</h1>
    <p>MCP endpoint: <code>/mcp</code></p>
  </main>
</body>
</html>
"""


async def _landing(request):
    return HTMLResponse(_LANDING_HTML)


# /favicon.ico carries PNG bytes and says so in its content type; every browser
# and favicon fetcher accepts that, and it saves shipping a separate .ico file.
PUBLIC_ROUTES = [
    Route("/", _landing, methods=["GET"]),
    Route("/favicon.ico", _asset_endpoint("logo-192.png", "image/png"), methods=["GET"]),
    Route("/favicon.svg", _asset_endpoint("logo.svg", "image/svg+xml"), methods=["GET"]),
    Route("/icon.png", _asset_endpoint("logo-192.png", "image/png"), methods=["GET"]),
]

PUBLIC_PATHS = frozenset(route.path for route in PUBLIC_ROUTES)
