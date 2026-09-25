"""Program logos: what an upload may be, and where it is stored.

The file type is read from the bytes rather than trusted from the
``Content-Type`` header. MCP callers fetch logos from arbitrary URLs, and a
server labelling a PNG ``application/octet-stream`` (or an HTML error page
``image/png``) is common enough that the header is not worth believing.
"""

import uuid

from fastapi import HTTPException

# Comfortably above any real logo, and under both the Vercel request body
# limit (4.5 MB) and the client's Server Action limit (next.config.ts).
MAX_LOGO_BYTES = 2 * 1024 * 1024

_EXTENSIONS = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "image/svg+xml": "svg",
}


def detect_logo_type(data: bytes) -> str:
    """The logo's MIME type, or a 400/413 if it is not an acceptable image."""
    if not data:
        raise HTTPException(400, "The logo file is empty.")
    if len(data) > MAX_LOGO_BYTES:
        raise HTTPException(413, "The logo must be 2 MB or smaller.")

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    # SVG is text: an optional XML prolog, comments or doctype, then <svg.
    # Browsers render it through <img>, where any script inside never runs.
    if b"<svg" in data[:2048].lower():
        return "image/svg+xml"

    raise HTTPException(400, "The logo must be a PNG, JPEG, WebP or SVG image.")


def logo_path(program_id: uuid.UUID, content_type: str) -> str:
    """A fresh object path per upload.

    Never reused, so a replaced logo cannot be served stale from a CDN or
    browser cache under the old URL - the program simply points somewhere new.
    """
    return f"programs/{program_id}/logo-{uuid.uuid4().hex[:12]}.{_EXTENSIONS[content_type]}"
