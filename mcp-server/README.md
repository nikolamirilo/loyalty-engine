# Loyalty Engine MCP Server

A hosted [MCP](https://modelcontextprotocol.io) server that exposes the
loyalty-engine API (`../api`) as tools for external AI agents, over the
Streamable HTTP transport. It never touches the database directly - every
tool calls the FastAPI service over HTTP, the same way any other API client
would.

## Status

Implements phases 1-3 of the rollout plan:

1. **Scaffold** - config, auth, HTTP client, server entrypoint.
2. **Read-only tools** - members, segments, rewards, tiers, balances,
   transactions, redemptions.
3. **Write tools** - create/update a member, earn/burn points, redeem a
   reward, trigger/verify DOI email.

Not yet implemented (a later, `admin`-scoped phase): deleting
members/rewards/tiers/segments, admin point adjustments, reward/tier/segment
CRUD, member custom-attribute definitions, and challenge assignment.

## Auth model

Two separate bearer tokens:

- **Inbound** (`MCP_CLIENT_TOKENS`) - one token per external agent allowed to
  call *this* server, each with its own scopes (`read`, `write`, or `admin`).
  Checked by `app/core/middleware.py` on every HTTP request before the MCP
  protocol handling even begins.
- **Outbound** (`LOYALTY_API_SERVICE_TOKEN`) - this server's own credential
  for calling the loyalty API, used for every request regardless of which
  external client asked. Never exposed to MCP clients.

Revoking or rescoping one external caller only means editing
`MCP_CLIENT_TOKENS` - it never requires rotating the loyalty API's own token.

Every tool calls `require_scope("read" | "write")` as its first line; a
caller whose token lacks that scope (and lacks `admin`, which satisfies any
scope) gets a tool error, not a silent partial result.

## Project layout

Mirrors `api/app`'s layering: `tools/` only translate MCP tool calls into
HTTP calls (no business logic - that already lives in the loyalty API);
`client/` is the one place that knows how to call the loyalty API;
`core/` holds config and auth, shared by everything else.

```
mcp-server/
├── requirements.txt
├── .env.example
└── app/
    ├── server.py           # ASGI entrypoint: `uvicorn app.server:app`
    ├── mcp_instance.py     # the shared FastMCP instance tools register onto
    ├── core/
    │   ├── config.py       # env vars - the only place they're read
    │   ├── auth.py         # client-token -> principal, require_scope()
    │   └── middleware.py   # ASGI bearer-auth middleware
    ├── client/
    │   └── loyalty_api_client.py   # thin async httpx wrapper around the loyalty API
    └── tools/              # one module per resource, mirrors api/app/routers/
        ├── members.py
        ├── segments.py
        ├── rewards.py
        ├── tiers.py
        ├── points.py
        ├── redemptions.py
        └── doi.py
```

## Setup

```bash
cd mcp-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in real values
```

`LOYALTY_API_BASE_URL` must point at a running instance of `../api`
(`uvicorn app.main:app` from the `api/` directory - see `api/README.md`).

## Running

```bash
uvicorn app.server:app --reload --port 8100
```

- MCP endpoint (Streamable HTTP): `http://localhost:8100/mcp`
- Unauthenticated health check: `http://localhost:8100/healthz`

Point an MCP client at the `/mcp` endpoint with
`Authorization: Bearer <one of MCP_CLIENT_TOKENS>`.

## Tool reference

| Scope | Tool | Loyalty API call |
|---|---|---|
| `read` | `list_members(q?, skip?, limit?)` | `GET /members` |
| `read` | `get_member(member_id)` | `GET /members/{id}` |
| `write` | `create_member(name, email, phone?, segment_ids?, custom_attributes?)` | `POST /members` |
| `write` | `update_member(member_id, ...)` | `PATCH /members/{id}` |
| `read` | `list_segments()` | `GET /segments` |
| `read` | `get_segment(segment_id)` | `GET /segments/{id}` |
| `read` | `list_rewards(active_only?, skip?, limit?)` | `GET /rewards` |
| `read` | `get_reward(reward_id)` | `GET /rewards/{id}` |
| `read` | `list_tiers()` | `GET /tiers` |
| `read` | `get_tier(tier_id)` | `GET /tiers/{id}` |
| `read` | `get_member_balance(member_id)` | `GET /members/{id}/balance` |
| `read` | `list_transactions(member_id, skip?, limit?)` | `GET /members/{id}/transactions` |
| `write` | `earn_points(member_id, points, description?)` | `POST /members/{id}/points/earn` |
| `write` | `burn_points(member_id, points, description?)` | `POST /members/{id}/points/burn` |
| `write` | `redeem_reward(member_id, reward_id)` | `POST /members/{id}/redeem/{reward_id}` |
| `read` | `list_member_redemptions(member_id, skip?, limit?)` | `GET /members/{id}/redemptions` |
| `write` | `trigger_doi(email?, member_id?, type?)` | `POST /doi/trigger` |
| `write` | `verify_doi(code, email?, member_id?)` | `POST /doi/verify` |

Tool inputs use the ORM's snake_case field names (e.g. `segment_ids`); tool
outputs pass the loyalty API's response straight through, already camelCase.

## Error handling

A non-2xx response from the loyalty API raises `LoyaltyAPIError` inside the
tool, which FastMCP turns into a tool error result carrying the API's own
`detail` message (e.g. `404: Member not found`).
