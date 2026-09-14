"""The icons this server advertises in its `initialize` response.

`app/assets/logo.svg` is a copy of the admin console's `client/public/logo.svg`,
kept here so this service stays deployable on its own. Change one and change the
other, and regenerate the PNG from the SVG (see mcp-server/README.md).

Icons are inlined as `data:` URIs rather than https URLs so a client never has
to reach another origin to draw them, and so the icon cannot break when an
unrelated deployment goes down.
"""

import base64
from pathlib import Path

from mcp.types import Icon

_ASSETS = Path(__file__).resolve().parent.parent / "assets"


def _data_uri(filename: str, mime_type: str) -> str:
    encoded = base64.b64encode((_ASSETS / filename).read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


# PNG first: the spec makes PNG support mandatory for any client that draws
# icons at all, while SVG is only a SHOULD, so a client picking the first entry
# it understands still gets something.
SERVER_ICONS = [
    Icon(src=_data_uri("logo-64.png", "image/png"), mimeType="image/png", sizes=["64x64"]),
    Icon(src=_data_uri("logo.svg", "image/svg+xml"), mimeType="image/svg+xml", sizes=["any"]),
]
