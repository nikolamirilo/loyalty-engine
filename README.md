# Loyalty Engine

A loyalty program platform: members earn and spend points, climb tiers, complete
challenges and redeem rewards. The repository holds three services that share one
Postgres database hosted on Supabase.

```mermaid
flowchart LR
    Staff["Staff"]
    People["Members"]
    Agents["AI agents<br/>Claude and other MCP clients"]

    Client["Next.js app<br/>admin console + member app"]
    MCP["MCP server<br/>FastMCP"]
    API["Loyalty API<br/>FastAPI"]
    DB[("Supabase<br/>Postgres")]

    Staff --> Client
    People --> Client
    Agents -->|"MCP over HTTP"| MCP
    Client -->|"HTTPS, bearer token"| API
    MCP -->|"HTTPS, bearer token"| API
    API --> DB
```

Only the API talks to the database. Everything else goes through the API, which
keeps one set of rules in one place.

## What is in here

| Folder | What it is | Read more |
|---|---|---|
| [`api/`](api) | The loyalty API. FastAPI and SQLAlchemy, owns all business logic and the only database connection. | [api/README.md](api/README.md) |
| [`client/`](client) | One Next.js project serving two apps: the staff admin console at `/admin`, and the member app at the root. | [client/README.md](client/README.md) |
| [`mcp-server/`](mcp-server) | Exposes the API to AI agents as MCP tools. Calls the API over HTTP like any other client. | [mcp-server/README.md](mcp-server/README.md) |
| [`supabase/`](supabase) | Hand written SQL migrations for changes `create_all` cannot make. | [supabase/README.md](supabase/README.md) |

## The domain in one table

| Concept | What it means |
|---|---|
| **Members** | People in the program. Name, email, phone, segments, points balance, custom attributes. |
| **Segments** | Named groups such as "VIP" or "Newsletter". A member can be in any number of them. |
| **Points** | Earned, spent, or adjusted by an admin. Every change is written to a transaction history. |
| **Tiers** | Conditions on points balance, purchase spend, segments and custom attributes, combined however a program likes, that apply an earn rate multiplier. Assigned automatically whenever any of them changes. |
| **Rewards** | The catalog members spend points on, with optional stock limits. |
| **Redemptions** | A reward a member took. Either `redeemed` (they paid points) or `assigned` (granted free). |
| **Challenges** | Goals a member works toward. Progress accumulates, and finishing pays out points, a reward, or both. |
| **Products and purchases** | A product catalog and what members bought. Used as a spend signal for targeting, not paid for with points. |
| **Events** | Things members do that another system reports, such as placing an order. Rules on each event decide what it earns: points, a reward, challenge progress, a segment, or updated member fields. |
| **DOI** | Double opt in email verification, by 6 digit code or by link. |

## Running it locally

Start the API first. The other two services are useless without it.

```bash
# 1. API on :8000
cd api
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set DATABASE_URL and API_TOKEN
uvicorn app.main:app --reload

# 2. Admin console on :3000
cd client
npm install
npm run dev

# 3. MCP server on :8100 (optional)
cd mcp-server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # point LOYALTY_API_BASE_URL at the API
uvicorn app.server:app --reload --port 8100
```

Swagger UI lives at `http://localhost:8000/docs`. Press **Authorize**, paste your
`API_TOKEN`, and you can try every endpoint from the browser.

## Tests

The API has a pytest suite that drives one member and one reward through the
main routes against a real Postgres, and reports the latency of every call. It
runs in GitHub Actions on any change under `api/`, and prints the same table
into the run summary.

```bash
cd api
pip install -r requirements.txt -r requirements-dev.txt
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/loyalty_test?sslmode=disable"
pytest
```

The suite refuses to run without `TEST_DATABASE_URL`, since it creates and
deletes rows. See [api/README.md](api/README.md#testing) for the details.

## House rules

These hold across all three services:

1. **Responses are camelCase.** `pointsBalance`, not `points_balance`. Request
   bodies accept either casing.
2. **Nothing but the API touches the database.** The console and the MCP server
   are HTTP clients, same as any third party would be.
3. **Keep the UI obvious.** Someone should be able to use a screen without being
   told how.
4. **Follow SOLID when placing code.** Routers translate HTTP, services hold
   logic shared between routers, models and schemas stay thin.

Project instructions for AI assistants live in [`.claude/CLAUDE.md`](.claude/CLAUDE.md).
