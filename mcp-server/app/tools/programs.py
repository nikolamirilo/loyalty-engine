"""Program discovery: which loyalty programs exist, so a caller can pick one.

The only tools here that are not program-scoped, mirroring the loyalty API's
own ``/programs`` router - this is how a caller finds out what it may pass as
the ``program`` argument everywhere else, so it cannot itself require one.

Creating and editing a program require ``write``. Deleting one is left out on
purpose and always will be: it cascades through every member, balance and
rule in the program, so it stays a manual action in the admin console.

``set_program_logo`` declares no annotations, like the DOI tools: it is one of
the few tools that reaches outside the system (it downloads the image), so it
belongs in a client's separate section for unhinted tools. See "How tools are
grouped" in the README.
"""

import ipaddress
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

import httpx

from app.client import loyalty_api_client as api
from app.core import annotations as ann
from app.core.auth import require_scope
from app.core.config import settings
from app.mcp_instance import mcp

# The loyalty API's own limit (api/app/services/program_branding.py). Checked
# while downloading, so a huge file is abandoned rather than read to the end.
MAX_LOGO_BYTES = 2 * 1024 * 1024


def _colors(primary_color: Optional[str], secondary_color: Optional[str]) -> Tuple[dict, tuple]:
    """Split the colour arguments into values to set and fields to clear.

    An empty string means "back to the stock colour", which the API spells as
    an explicit null - and None is already taken by "leave unchanged".
    """
    body, clear = {}, []
    for field, value in (("primary_color", primary_color), ("secondary_color", secondary_color)):
        if value == "":
            clear.append(field)
        elif value is not None:
            body[field] = value
    return body, tuple(clear)


def _check_public_url(url: str) -> None:
    """Refuse anything but a public http(s) URL, so the tool cannot be pointed
    at the server's own network."""
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if parts.scheme not in ("http", "https") or not host:
        raise ValueError("image_url must be an http or https URL.")
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".internal"):
        raise ValueError("image_url must point at a public host.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return  # a hostname, not an IP literal
    if not address.is_global:
        raise ValueError("image_url must point at a public host.")


async def _download(url: str) -> Tuple[bytes, str]:
    _check_public_url(url)
    async with httpx.AsyncClient(
        follow_redirects=True, timeout=settings.request_timeout_seconds
    ) as client:
        async with client.stream("GET", url) as response:
            if response.status_code >= 400:
                raise ValueError(f"Could not download the image: HTTP {response.status_code}.")
            _check_public_url(str(response.url))  # after any redirects
            chunks, size = [], 0
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > MAX_LOGO_BYTES:
                    raise ValueError("The image is larger than 2 MB.")
                chunks.append(chunk)
            content_type = response.headers.get("content-type", "application/octet-stream")
    # The API reads the real type from the bytes; the header is only a label.
    return b"".join(chunks), content_type.split(";")[0].strip()


@mcp.tool(title="List Programs", annotations=ann.READ)
async def list_programs() -> List[Dict[str, Any]]:
    """List the loyalty programs on this deployment, oldest first.

    Call this first when the user has not said which program to work in, then
    pass the chosen program's `slug` as the `program` argument to every other
    tool - members, points, rewards, challenges and the rest are all scoped to
    one program, and the same member can hold a different balance in each.

    The program with `isDefault` true is the one used when `program` is
    omitted. Each entry has `id`, `name`, `slug`, `description`, `isDefault`,
    the branding fields `logoUrl`, `primaryColor` and `secondaryColor` (null
    when the program uses the stock look), and `createdAt`.
    """
    require_scope("read")
    return await api.get("/programs")


@mcp.tool(title="Get Program", annotations=ann.READ)
async def get_program(program_id: str) -> Dict[str, Any]:
    """Get a single program by id.

    Takes the program's UUID specifically, not its slug - use `list_programs`
    to look one up by name. Other tools' `program` argument accepts either.
    """
    require_scope("read")
    return await api.get(f"/programs/{program_id}")


@mcp.tool(title="Create Program", annotations=ann.WRITE)
async def create_program(
    name: str,
    slug: Optional[str] = None,
    description: Optional[str] = None,
    is_default: bool = False,
    primary_color: Optional[str] = None,
    secondary_color: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a loyalty program. `slug` (lowercase letters, digits and single
    hyphens) is what other tools accept as `program`; omit it to derive one
    from `name`. `is_default` true makes this the program used when `program`
    is omitted, taking that over from the current default.

    `primary_color` and `secondary_color` brand the admin console and member
    app while this program is selected, as `#rrggbb` hex. Primary drives
    buttons, links and highlights, so pick one that reads on white (for Lidl,
    the blue `#0050aa`, not the yellow). Secondary is the accent on the member
    tier card. Add a logo afterwards with `set_program_logo`.

    Members are shared across programs, so every existing member is enrolled
    in the new program straight away, at zero points.
    """
    require_scope("write")
    colors, _ = _colors(primary_color, secondary_color)
    body = {"name": name, "slug": slug, "description": description, "is_default": is_default, **colors}
    return await api.post("/programs", body)


@mcp.tool(title="Update Program", annotations=ann.WRITE)
async def update_program(
    program_id: str,
    name: Optional[str] = None,
    slug: Optional[str] = None,
    description: Optional[str] = None,
    is_default: Optional[bool] = None,
    primary_color: Optional[str] = None,
    secondary_color: Optional[str] = None,
) -> Dict[str, Any]:
    """Update a program by UUID. Only the fields provided are changed.

    Changing `slug` breaks any caller still passing the old one as `program`.
    `is_default` can only be set to true: to move the default, make another
    program the default rather than unsetting this one.

    `primary_color` and `secondary_color` are `#rrggbb` hex; pass an empty
    string to put one back to the stock colour. The logo has its own tools,
    `set_program_logo` and `remove_program_logo`.
    """
    require_scope("write")
    colors, clear = _colors(primary_color, secondary_color)
    body = {"name": name, "slug": slug, "description": description, "is_default": is_default, **colors}
    return await api.patch(f"/programs/{program_id}", body, clear=clear)


# Deliberately unannotated - see the module docstring.
@mcp.tool(title="Set Program Logo")
async def set_program_logo(program_id: str, image_url: str) -> Dict[str, Any]:
    """Download an image from `image_url` and make it the program's logo.

    The logo shows in the admin console sidebar, the program switchers and the
    member app header while this program is selected. PNG, JPEG, WebP or SVG,
    up to 2 MB, from a public http(s) URL - a transparent PNG or an SVG looks
    best. The file is stored in the loyalty engine's own storage, so the
    source URL does not need to stay up. Replaces any previous logo.

    Takes the program's UUID (see `list_programs`). Returns the updated
    program, with `logoUrl` pointing at the stored copy.
    """
    require_scope("write")
    content, content_type = await _download(image_url)
    return await api.put_file(f"/programs/{program_id}/logo", content, content_type)


@mcp.tool(title="Remove Program Logo", annotations=ann.DELETE)
async def remove_program_logo(program_id: str) -> Dict[str, Any]:
    """Remove the program's logo, going back to the stock one. The stored file
    is deleted. Takes the program's UUID; returns the updated program."""
    require_scope("write")
    return await api.delete(f"/programs/{program_id}/logo")
