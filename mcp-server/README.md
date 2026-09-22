# Loyalty Engine MCP Server

Exposes the [loyalty API](../api) to AI agents as [MCP](https://modelcontextprotocol.io)
tools, over the Streamable HTTP transport. It never touches the database. Every
tool turns into an HTTP call to the API, the same way any other client would do
it, so the business rules stay in one place.

```mermaid
flowchart LR
    Agent["MCP client<br/>Claude, or another agent"]
    MW["middleware.py<br/>checks the inbound token"]
    Tool["tools/<br/>require_scope() then call the client"]
    Client["loyalty_api_client.py<br/>attaches the service token"]
    API["Loyalty API"]

    Agent -->|"MCP_CLIENT_TOKENS"| MW
    MW --> Tool
    Tool --> Client
    Client -->|"LOYALTY_API_SERVICE_TOKEN"| API
```

## Status

Four phases are done:

1. **Scaffold**, config, auth, HTTP client, server entrypoint.
2. **Read tools**, members, segments, rewards, tiers, balances, transactions,
   redemptions.
3. **Write tools**, create and update a member, earn and burn points, redeem a
   reward, trigger and verify DOI email.
4. **Challenges, prizes, products and purchases**, the full challenge lifecycle
   plus the catalog behind purchase based flows.

Held back for a later admin scope: deleting members, rewards, tiers and segments,
admin point adjustments, reward, tier and segment writes, and member custom
attribute definitions.

Member sign in (`/auth/signup`, `/auth/login`, `/auth/verify`) is deliberately
left off. It is a credential flow, and brokering it through an external agent
would be the wrong place for it.

## Two tokens, on purpose

| | Inbound | Outbound |
|---|---|---|
| Variable | `MCP_CLIENT_TOKENS` | `LOYALTY_API_SERVICE_TOKEN` |
| Answers | Which agent is calling this server, and what may it do | How this server proves itself to the loyalty API |
| Checked by | `app/core/middleware.py`, before any MCP handling | Sent on every outbound call, whoever asked |
| Seen by clients | Their own token only | Never |

The point of the split is revocation. Dropping a misbehaving caller means editing
`MCP_CLIENT_TOKENS`. The loyalty API's own credential never has to rotate.

Scopes are `read`, `write` and `admin`, where `admin` satisfies any check. Every
tool calls `require_scope(...)` on its first line, so a caller without the scope
gets a tool error rather than a quiet partial result.

## Project layout

Mirrors `api/app`. Tools only translate MCP calls into HTTP calls, since the
logic already lives in the API.

```
mcp-server/
├── requirements.txt
├── .env.example
└── app/
    ├── server.py           # ASGI entrypoint: `uvicorn app.server:app`
    ├── mcp_instance.py     # the shared MCPServer instance tools register onto
    ├── core/
    │   ├── config.py       # env vars, read in one place
    │   ├── auth.py         # token to principal, require_scope()
    │   ├── annotations.py  # the behaviour hints each tool declares
    │   ├── branding.py     # the icons sent in the initialize response
    │   └── middleware.py   # ASGI bearer auth
    ├── assets/
    │   ├── logo.svg        # copy of client/public/logo.svg
    │   └── logo-64.png     # rendered from that SVG
    ├── client/
    │   └── loyalty_api_client.py   # the only module that knows the API
    └── tools/              # one module per resource, mirrors api/app/routers/
        ├── members.py
        ├── points.py
        ├── challenges.py
        ├── redemptions.py
        ├── rewards.py
        ├── products.py
        ├── purchases.py
        ├── segments.py
        ├── tiers.py
        └── doi.py
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

| Variable | What it is for |
|---|---|
| `LOYALTY_API_BASE_URL` | Where the loyalty API is running. |
| `LOYALTY_API_SERVICE_TOKEN` | The API's own `API_TOKEN`. |
| `MCP_CLIENT_TOKENS` | JSON array of callers, each with a token, a name and scopes. |
| `LOYALTY_API_TIMEOUT_SECONDS` | Optional, defaults to 15. |

## Running

```bash
uvicorn app.server:app --reload --port 8100
```

- MCP endpoint: `http://localhost:8100/mcp`
- Health check, no auth: `http://localhost:8100/healthz`

Point a client at `/mcp` with `Authorization: Bearer <one of MCP_CLIENT_TOKENS>`.

## Tool reference

40 tools. Inputs use snake_case field names, outputs pass the API response
straight through, already camelCase. The headings below group by domain for
reading only; the title a client actually shows is verb first, see
[How tools are grouped](#how-tools-are-grouped).

**Members**

| Scope | Tool | API call |
|---|---|---|
| `read` | `list_members(q?, skip?, limit?)` | `GET /members` |
| `read` | `get_member(member_id)` | `GET /members/{id}` |
| `write` | `create_member(name, email, phone?, segment_ids?, custom_attributes?)` | `POST /members` |
| `write` | `update_member(member_id, ...)` | `PATCH /members/{id}` |

**Points**

| Scope | Tool | API call |
|---|---|---|
| `read` | `get_member_balance(member_id)` | `GET /members/{id}/balance` |
| `read` | `list_transactions(member_id, skip?, limit?)` | `GET /members/{id}/transactions` |
| `write` | `earn_points(member_id, points, description?)` | `POST /members/{id}/points/earn` |
| `write` | `burn_points(member_id, points, description?)` | `POST /members/{id}/points/burn` |

**Rewards, redemptions and prizes**

| Scope | Tool | API call |
|---|---|---|
| `read` | `list_rewards(active_only?, skip?, limit?)` | `GET /rewards` |
| `read` | `get_reward(reward_id)` | `GET /rewards/{id}` |
| `write` | `redeem_reward(member_id, reward_id)` | `POST /members/{id}/redeem/{rewardId}` |
| `read` | `list_member_redemptions(member_id, skip?, limit?)` | `GET /members/{id}/redemptions` |
| `write` | `assign_prize(member_id, reward_id)` | `POST /members/{id}/prizes/{rewardId}` |
| `read` | `list_member_prizes(member_id, source?, skip?, limit?)` | `GET /members/{id}/prizes` |

**Challenges**

| Scope | Tool | API call |
|---|---|---|
| `write` | `create_challenge(name, target_value?, reward_points?, reward_id?, ...)` | `POST /challenges` |
| `read` | `list_challenges(active_only?, skip?, limit?)` | `GET /challenges` |
| `read` | `get_challenge(challenge_id)` | `GET /challenges/{id}` |
| `write` | `update_challenge(challenge_id, ...)` | `PATCH /challenges/{id}` |
| `write` | `delete_challenge(challenge_id)` | `DELETE /challenges/{id}` |
| `write` | `assign_challenge_to_member(member_id, challenge_id)` | `POST /members/{id}/challenges/{id}` |
| `read` | `list_member_challenges(member_id, status?, skip?, limit?)` | `GET /members/{id}/challenges` |
| `read` | `get_member_challenge_progress(member_id, challenge_id)` | `GET /members/{id}/challenges/{id}` |
| `write` | `update_challenge_progress(member_id, challenge_id, amount?, description?)` | `POST /members/{id}/challenges/{id}/progress` |
| `write` | `complete_challenge(member_id, challenge_id)` | `POST /members/{id}/challenges/{id}/complete` |
| `write` | `unassign_challenge(member_id, challenge_id)` | `DELETE /members/{id}/challenges/{id}` |
| `write` | `assign_challenge_to_segment(challenge_id, segment_id)` | `POST /challenges/{id}/assign-segment` |

**Products and purchases**

| Scope | Tool | API call |
|---|---|---|
| `write` | `create_product(name, price_cents, ...)` | `POST /products` |
| `read` | `list_products(active_only?, skip?, limit?)` | `GET /products` |
| `read` | `get_product(product_id)` | `GET /products/{id}` |
| `write` | `update_product(product_id, ...)` | `PATCH /products/{id}` |
| `write` | `delete_product(product_id)` | `DELETE /products/{id}` |
| `write` | `purchase_product(member_id, product_id, quantity?)` | `POST /members/{id}/purchases` |
| `read` | `list_member_purchases(member_id, skip?, limit?)` | `GET /members/{id}/purchases` |
| `read` | `get_member_purchase_stats(member_id, days?)` | `GET /members/{id}/purchase-stats` |

**Segments, tiers and DOI**

| Scope | Tool | API call |
|---|---|---|
| `read` | `list_segments()` | `GET /segments` |
| `read` | `get_segment(segment_id)` | `GET /segments/{id}` |
| `read` | `list_tiers()` | `GET /tiers` |
| `read` | `get_tier(tier_id)` | `GET /tiers/{id}` |
| `write` | `trigger_doi(email?, member_id?, type?)` | `POST /doi/trigger` |
| `write` | `verify_doi(code, email?, member_id?)` | `POST /doi/verify` |

## Adding a tool

1. Add the function to the matching module in `app/tools/`, or create a new
   module and import it in `app/tools/__init__.py`.
2. Give it a verb-first `title` in the `"<Verb> <object>"` shape, such as
   `Create Challenge` or `List Member Purchases`. No domain prefix. See
   [How tools are grouped](#how-tools-are-grouped).
3. Pass `annotations=ann.READ`, `ann.WRITE`, `ann.DELETE` or `ann.OUTBOUND`
   from `app/core/annotations.py`, matching the scope in the next step.
   `ann.DELETE` is for tools that remove a record and nothing else.
4. Call `require_scope("read")` or `require_scope("write")` first.
5. Call the API through `app.client.loyalty_api_client`, never `httpx` directly.
   That keeps the transport mockable and the service token in one place.
6. Add a row to the table above.

## Error handling

A non 2xx answer from the loyalty API raises `LoyaltyAPIError` inside the tool.
MCP turns that into a tool error carrying the API's own `detail` message, for
example `404: Member not found`.

## How tools are grouped

A client sorts this server's 42 tools along two axes, and they work differently.

### By behaviour, which the protocol does support

Every tool declares `annotations` from `app/core/annotations.py`:

| Preset | Bucket | Tools | `readOnlyHint` | `destructiveHint` | `openWorldHint` |
|---|---|---|---|---|---|
| `READ` | read | 22 | `true` | `false` | `false` |
| `WRITE` | write | 15 | `false` | `false` | `false` |
| `DELETE` | delete | 3 | `false` | `true` | `false` |
| `OUTBOUND` | write | 2 | `false` | `false` | `true` |

`DELETE` means the tool removes a record and nothing else, which is three of
them: `delete_challenge`, `delete_product` and `unassign_challenge`.
`burn_points` is a `WRITE` despite spending a balance, because what it actually
does is append a transaction; no record goes away. `OUTBOUND` is the two DOI
tools, the only ones that reach an address outside the system. `openWorldHint`
is `false` everywhere else because these tools address one loyalty API holding
a closed, enumerable set of entities.

These four flags are the whole vocabulary the protocol gives a server for this.
`destructiveHint` is the only thing separating a write from a delete, so the
read / write / delete split above is exactly as fine-grained as MCP allows.
Note that `destructiveHint` defaults to *true* when omitted, so the writes have
to say `false` out loud rather than stay silent, otherwise they read as deletes.

**What the client does with it is the client's business.** Claude's connector
settings screen currently folds both non-read buckets into one heading,
**Write/delete tools**, opposite **Read-only tools**; a tool declaring no
annotations at all has nothing to sort by and lands in a flat **Other tools**
list, which is where all 42 sat before these were added. A server cannot rename
those headings or ask for a third one, so `DELETE` will not draw its own section
until a client chooses to read `destructiveHint` that way. What it does do today
is mark those three tools as irreversible, which is what drives a client's
confirmation prompt before it calls one.

The hints are hints. `require_scope(...)` on the tool's first line is the
actual gate, and it runs whatever a client believes.

### By domain, which the protocol does not support

There is no way to tell a client that `earn_points` belongs to a "Points"
group. A `Tool` carries a name, a title, a description, its schemas, icons and
`_meta`, and nothing else, so a server cannot ask for the headings used in the
tool reference above. [SEP-1300](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1300)
proposed exactly that, groups and tags on `tools/list`, and was closed without
being adopted; the 2026-07-28 spec does not contain it.

What a client does use is the title, with display precedence `title`, then
`annotations.title`, then `name`, and it orders its list by that display name.
Titles here used to exploit that with a `"<Domain>: <action>"` prefix, so
related tools sorted together and faked the missing grouping.

That prefix has been dropped. The behaviour annotations above already split the
list into read and write, and inside a bucket the prefix only pushed the word
that identifies the tool to the right, where it is slower to scan:

| Was | Now |
|---|---|
| `Challenges: Assign to member` | `Assign Challenge to Member` |
| `Challenges: Create` | `Create Challenge` |
| `Points: Burn` | `Burn Points` |

Titles are now verb first, reading as the action the tool performs. The trade is
that sorting no longer clusters a domain: `Create Challenge` lands beside
`Create Product`, and `Get Challenge` sits well away from both. That is the
better default once the read/write split has already halved the list, since what
a caller scans for is the verb.

## Branding

The server sends its logo in the `initialize` response, as `icons` on
`serverInfo`. Two entries go out, together about 6.5 KB:

| File | Type | Sizes | Why |
|---|---|---|---|
| `app/assets/logo-64.png` | `image/png` | `64x64` | Every client that draws icons has to support PNG. Listed first. |
| `app/assets/logo.svg` | `image/svg+xml` | `any` | Scales cleanly for clients that support it. |

Both are inlined as `data:` URIs rather than https links, so drawing the icon
never depends on another deployment being reachable.

`app/assets/logo.svg` is a copy of the admin console's `client/public/logo.svg`,
which keeps this service deployable on its own. Change one and change the other,
then re-render the PNG:

```bash
pip install cairosvg
python -c "import cairosvg; cairosvg.svg2png(url='app/assets/logo.svg', write_to='app/assets/logo-64.png', output_width=64, output_height=64)"
```

`cairosvg` is a one off tool for that command, not a runtime dependency, so it
stays out of `requirements.txt`.

Worth knowing: this is the correct shape and there is nothing further to do on
the server. Rendering is entirely up to the client, and claude.ai does not read
`serverInfo.icons` for custom connectors yet, so the connector still shows a
generic avatar. That is tracked in
[claude-ai-mcp#152](https://github.com/anthropics/claude-ai-mcp/issues/152),
open and unanswered, alongside
[claude-code#95558](https://github.com/anthropics/claude-code/issues/95558) for
the CLI. Branded icons on Claude's own connectors are configured by Anthropic,
not sent by those servers. No server-side change, and no other MCP library,
moves this: the icon appears when client support lands.

The `Icon` type also carries a `theme` field (`light` or `dark`), and `Tool`
carries its own `icons` list. Neither is used here, since no client draws
either yet.
