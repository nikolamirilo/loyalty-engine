"""Thin async HTTP client for the loyalty-engine REST API.

The MCP server never touches the database directly - every tool goes
through this module, which is the only place that knows the loyalty API's
base URL and service token. Tool modules call the functions here rather than
using httpx directly, so the transport can be mocked in tests without
touching tool code.

Request bodies use the ORM's own snake_case field names (e.g. ``segment_ids``,
not ``segmentIds``) - the loyalty API's schemas accept either casing
(``populate_by_name=True``), so no camelCase conversion is needed here.
Responses are returned exactly as the API sends them (already camelCase) and
passed straight through by the calling tool.
"""

from typing import Any, Dict, Optional, Tuple

import httpx

from app.core.config import settings


class LoyaltyAPIError(Exception):
    """A non-2xx response from the loyalty API, carrying the `detail` message
    the API returned so it can be surfaced back to the calling agent."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{status_code}: {detail}")


_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.loyalty_api_base_url,
            headers={"Authorization": f"Bearer {settings.loyalty_api_service_token}"},
            timeout=settings.request_timeout_seconds,
        )
    return _client


async def aclose() -> None:
    """Release the pooled connection. Call on server shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _drop_none(values: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in values.items() if v is not None}


async def _request(
    method: str,
    path: str,
    *,
    json_body: Optional[dict] = None,
    params: Optional[dict] = None,
    program: Optional[str] = None,
    content: Optional[bytes] = None,
    content_type: Optional[str] = None,
) -> Any:
    program = program or settings.default_program
    # httpx merges request headers into the client's, so the Authorization
    # header set once in _get_client() survives.
    headers = {"X-Program-Id": program} if program else {}
    if content_type:
        headers["Content-Type"] = content_type
    response = await _get_client().request(
        method, path, json=json_body, params=params, content=content, headers=headers or None
    )
    if response.status_code >= 400:
        detail = response.text
        try:
            detail = response.json().get("detail", detail)
        except ValueError:
            pass
        raise LoyaltyAPIError(response.status_code, detail)
    if response.status_code == 204 or not response.content:
        return None
    return response.json()


async def get(
    path: str, params: Optional[dict] = None, *, program: Optional[str] = None
) -> Any:
    return await _request(
        "GET", path, params=_drop_none(params or {}), program=program
    )


async def post(
    path: str, json_body: Optional[dict] = None, *, program: Optional[str] = None
) -> Any:
    return await _request(
        "POST", path, json_body=_drop_none(json_body or {}), program=program
    )


async def patch(
    path: str,
    json_body: Optional[dict] = None,
    *,
    program: Optional[str] = None,
    clear: Tuple[str, ...] = (),
) -> Any:
    """`clear` names fields to send as an explicit null - how a PATCH resets a
    value (e.g. unlimited stock) now that every other None is dropped as
    "leave unchanged"."""
    body = {**_drop_none(json_body or {}), **{field: None for field in clear}}
    return await _request("PATCH", path, json_body=body, program=program)


async def put_file(
    path: str, content: bytes, content_type: str, *, program: Optional[str] = None
) -> Any:
    """PUT a raw binary body, e.g. a program logo."""
    return await _request(
        "PUT", path, content=content, content_type=content_type, program=program
    )


async def delete(path: str, *, program: Optional[str] = None) -> Any:
    return await _request("DELETE", path, program=program)
