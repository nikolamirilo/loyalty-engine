"""Application configuration for the MCP server.

The single place environment variables are read, mirroring the pattern in
``api/app/core/config.py``: everything else imports ``settings`` rather than
calling ``os.getenv``, so required config fails loudly at import time in one
spot instead of at the first request that happens to need it.
"""

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, FrozenSet

from dotenv import load_dotenv

load_dotenv()


def _required(name: str, hint: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set. {hint}")
    return value


def _optional(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


@dataclass(frozen=True)
class ClientPrincipal:
    """An external MCP caller: a human-readable name for logging/audit, and
    the scopes it's allowed to invoke tools under. Looked up by bearer token
    - see ``Settings.client_tokens``."""

    name: str
    scopes: FrozenSet[str]


@dataclass(frozen=True)
class Settings:
    """Validated runtime configuration."""

    loyalty_api_base_url: str
    # The loyalty API's own bearer token (its API_TOKEN). Used for every
    # outbound call this server makes, regardless of which external MCP
    # client is asking - kept separate from client_tokens below so a
    # revoked/compromised external caller never needs this credential
    # rotated too.
    loyalty_api_service_token: str
    # Bearer token -> principal, for callers of *this* server.
    client_tokens: Dict[str, ClientPrincipal]
    request_timeout_seconds: float = 15.0

    project_name: str = "Loyalty Engine MCP Server"
    version: str = "0.1.0"


def _parse_client_tokens(raw: str) -> Dict[str, ClientPrincipal]:
    """Parse ``MCP_CLIENT_TOKENS``: a JSON array of
    ``{"token": "...", "name": "...", "scopes": ["read", "write"]}`` entries,
    one per external agent allowed to call this server. ``scopes`` is any of
    "read", "write", "admin" - "admin" implies the other two.
    """
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"MCP_CLIENT_TOKENS is not valid JSON: {exc}") from exc
    if not isinstance(entries, list) or not entries:
        raise RuntimeError("MCP_CLIENT_TOKENS must be a non-empty JSON array.")

    tokens: Dict[str, ClientPrincipal] = {}
    for entry in entries:
        token = entry["token"]
        tokens[token] = ClientPrincipal(
            name=entry["name"],
            scopes=frozenset(entry["scopes"]),
        )
    return tokens


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        loyalty_api_base_url=_required(
            "LOYALTY_API_BASE_URL",
            "Add the base URL of the loyalty-engine FastAPI service (e.g. https://api.example.com).",
        ).rstrip("/"),
        loyalty_api_service_token=_required(
            "LOYALTY_API_SERVICE_TOKEN",
            "Add the loyalty API's bearer token (its API_TOKEN).",
        ),
        client_tokens=_parse_client_tokens(
            _required(
                "MCP_CLIENT_TOKENS",
                "Add a JSON array of allowed callers, e.g. "
                '\'[{"token": "...", "name": "partner-a", "scopes": ["read", "write"]}]\'.',
            )
        ),
        request_timeout_seconds=float(_optional("LOYALTY_API_TIMEOUT_SECONDS", "15") or 15),
    )


settings = get_settings()
