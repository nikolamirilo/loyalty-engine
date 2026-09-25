"""File storage for program branding assets (logos).

Files go to a public Supabase Storage bucket, so the console and the member
app can show a logo straight from its URL with no extra round trip through
the API. Only the API writes there, with the service role key; nothing else
holds a credential for the bucket.

``ObjectStorage`` is the seam the routes depend on (via ``get_storage``), so a
test can swap in an in-memory fake without touching Supabase.
"""

import logging
from typing import Protocol
from urllib.parse import quote

import httpx
from fastapi import Depends, HTTPException

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

# Well under the serverless function budget, like the email sender's.
STORAGE_TIMEOUT_SECONDS = 10


class ObjectStorage(Protocol):
    def upload(self, path: str, data: bytes, content_type: str) -> str:
        """Store ``data`` at ``path`` and return its public URL."""

    def delete_url(self, url: str) -> None:
        """Remove the object behind a URL ``upload`` returned. Best effort."""


class SupabaseStorage:
    """A public bucket in Supabase Storage, spoken to over its REST API."""

    def __init__(self, base_url: str, service_key: str, bucket: str) -> None:
        self._base_url = base_url
        self._bucket = bucket
        self._headers = {"Authorization": f"Bearer {service_key}", "apikey": service_key}

    def _public_prefix(self) -> str:
        return f"{self._base_url}/storage/v1/object/public/{self._bucket}/"

    def upload(self, path: str, data: bytes, content_type: str) -> str:
        try:
            response = httpx.post(
                f"{self._base_url}/storage/v1/object/{self._bucket}/{quote(path)}",
                content=data,
                headers={**self._headers, "Content-Type": content_type, "x-upsert": "true"},
                timeout=STORAGE_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as exc:
            logger.exception("Storage upload to %s failed", path)
            raise HTTPException(502, "Could not reach file storage. Please try again.") from exc
        if response.status_code >= 400:
            logger.error(
                "Storage rejected upload to %s: %s %s", path, response.status_code, response.text
            )
            raise HTTPException(502, "File storage rejected the upload.")
        return self._public_prefix() + quote(path)

    def delete_url(self, url: str) -> None:
        prefix = self._public_prefix()
        # A URL we did not hand out (another bucket, an old project) is not ours
        # to delete; leave it rather than guess.
        if not url.startswith(prefix):
            return
        try:
            # The remainder is the object path, still URL-quoted as upload built it.
            httpx.delete(
                f"{self._base_url}/storage/v1/object/{self._bucket}/{url[len(prefix):]}",
                headers=self._headers,
                timeout=STORAGE_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError:
            # An orphaned file costs a few kilobytes; failing the request that
            # replaced or removed the logo over it would cost the admin a retry.
            logger.warning("Could not delete stored file %s", url, exc_info=True)


def get_optional_storage() -> ObjectStorage | None:
    """FastAPI dependency for routes that only *clean up* files.

    Removing a logo or deleting a program must still work on a deployment
    without Storage configured; the file is then simply left behind.
    """
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None
    return SupabaseStorage(
        settings.supabase_url, settings.supabase_service_role_key, settings.storage_bucket
    )


def get_storage(
    storage: ObjectStorage | None = Depends(get_optional_storage),
) -> ObjectStorage:
    """FastAPI dependency: the configured storage, or a clear 503 if there is none.

    Checked per request rather than at boot, so a deployment that never
    uploads a logo does not need Supabase Storage configured at all. Built on
    ``get_optional_storage`` so overriding that one dependency (as the tests
    do) swaps the storage behind both.
    """
    if storage is None:
        raise HTTPException(
            503,
            "Logo uploads are not configured. Set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY on the API.",
        )
    return storage
