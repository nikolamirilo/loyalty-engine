# Loyalty API

The service that owns the loyalty program. FastAPI, SQLAlchemy, and a Supabase
Postgres database. Everything else in the platform, the [admin console](../client)
and the [MCP server](../mcp-server), talks to this API over HTTP. Nothing else
opens a database connection.

Every route except `/health` and the docs requires a bearer token.

## What it does

| Area | Summary |
|---|---|
| **Members** | Name, email, phone, segment memberships, points balance, custom attributes. |
| **Segments** | Named groups such as "VIP". A member belongs to any number of them, and members can be bulk assigned. |
| **Points** | Earn, spend, and admin adjustments, each written to a transaction history. |
| **Tiers** | Point thresholds that apply an earn rate multiplier, assigned automatically as a balance moves. |
| **Rewards** | The redeemable catalog, with optional stock limits. |
| **Redemptions and prizes** | Members spend points on a reward, or staff grant one for free. |
| **Challenges** | Goals with a target value. Progress accrues, and completion pays out points, a reward, or both. Can be pushed to a whole segment at once. |
| **Products and purchases** | A catalog members buy from on unlimited credit. Purchases are a spend signal, not a points transaction. |
| **DOI** | Double opt in email verification, by 6 digit code or by link. |
| **Member auth** | Passwordless sign in for the member app, by emailed code. |
| **Member attributes** | Admin defined custom fields, with type validation. |

## Project layout

Code is layered by job. A router never imports another router. Anything shared,
such as `apply_tier`, lives in `app/services` instead.

```mermaid
flowchart LR
    HTTP["HTTP request"] --> R["routers/<br/>validate and shape"]
    R --> S["services/<br/>business logic"]
    S --> M["models/<br/>SQLAlchemy ORM"]
    M --> DB[("Postgres")]
    R -.->|"plain CRUD"| M
    R --> Sch["schemas/<br/>request and response"]
```

- **routers** translate HTTP to ORM and back. Plain reads and writes may touch a
  model directly. Anything more goes to a service.
- **services** hold logic shared between routers, or logic too involved for a
  route function.
- **models** are the ORM classes, **schemas** the Pydantic shapes, mirrored one
  to one.

```
api/
├── main.py                       # Shim: `from app.main import app`, kept for old deploy config
├── requirements.txt
├── .env.example
├── tests/                        # Standalone regression scripts, see Testing
├── scripts/                      # One off data migrations
└── app/
    ├── main.py                   # Creates the app, wires routers, handles DB errors
    ├── core/
    │   ├── config.py             # Settings, the only place env vars are read
    │   ├── database.py           # Engine, session, Base, get_db
    │   └── security.py           # Bearer token dependency
    ├── models/                   # One module per resource
    ├── schemas/                  # Pydantic shapes, mirrored with models/
    ├── services/
    │   ├── tiers.py              # apply_tier, re-applied on every balance change
    │   ├── points.py             # record_transaction, the only path that moves total_points
    │   ├── rewards.py            # availability checks and prize granting
    │   ├── challenges.py         # expiry, segment fan out, completion rewards
    │   ├── products.py           # purchase recording and spend stats
    │   ├── member_auth.py        # passwordless member login codes
    │   ├── email_verification.py # DOI codes and links
    │   ├── email_sending.py      # Resend transport
    │   ├── segments.py
    │   └── custom_attributes.py  # type validation for member custom attributes
    └── routers/                  # members, member_attributes, points, rewards,
                                  # redemptions, products, purchases, challenges,
                                  # segments, tiers, doi, auth
```

SQL migrations live in [`../supabase/migrations`](../supabase), not in this folder.

> A few files still sit at the top of `api/`: `models.py`, `schemas.py`,
> `database.py`, `auth.py`, `custom_attributes.py` and a `routers/` folder. They
> are leftovers from before the move into `app/` and nothing imports them. Read
> `app/` instead.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Four variables are required. The app refuses to start without them, which is on
purpose: a missing value fails loudly at import rather than at the first request
that happens to need it.

| Variable | Required | What it is for |
|---|---|---|
| `DATABASE_URL` | Yes | Supabase Postgres connection string, transaction pooler. |
| `API_TOKEN` | Yes | The bearer token every route checks. |
| `RESEND_API_KEY` | Yes | Sends DOI and login emails through [Resend](https://resend.com). |
| `DOI_FROM_EMAIL` | Yes | Sender address, on a domain verified in Resend. |
| `CLIENT_BASE_URL` | Only for DOI links | Public base URL of the client app, used to build the emailed link. |

### Connecting to Supabase

1. In the Supabase dashboard, open **Project Settings, Database, Connection string**.
2. Copy the **Connection pooling** URI in **Transaction mode**, port `6543`.
3. Replace `[YOUR-PASSWORD]` with your database password.

```
DATABASE_URL=postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
```

Use transaction mode. Session mode on port `5432` gives each client its own
Postgres backend out of a budget of about 15, which a serverless deployment
exhausts almost at once:

```
FATAL: (EMAXCONNSESSION) max clients reached in session mode - max clients are limited to pool_size: 15
```

A session mode URL is rewritten to `6543` at startup with a warning in the logs,
but fix `DATABASE_URL` rather than leaning on that. If the database is
unreachable, the API answers `503` with a JSON body instead of crashing the
request.

SSL is on automatically. Tables are created on first run. Changes to tables that
already exist need a migration, see [supabase/README.md](../supabase/README.md).

## Running

```bash
uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`, press **Authorize** and paste your
  token to try endpoints from the browser.

`uvicorn main:app --reload` still works too. `api/main.py` is a thin shim kept for
deploy config that points at it.

## Authentication

```
Authorization: Bearer <API_TOKEN>
```

Everything except `/health` and the docs requires it. A missing or wrong token
gets `401` or `403`.

Note that this is the *service* token, proving a trusted backend is calling. It
is separate from member sign in under `/auth`, which identifies a person in the
program and returns their record.

## JSON casing

Responses are always camelCase (`pointsBalance`, `createdAt`, `isActive`), built
from snake_case Python fields by a shared `CamelModel` base in
`app/schemas/base.py`. Request bodies accept either casing, so older snake_case
payloads keep working.

## How points and tiers stay in sync

Every change to a balance funnels through one function. That is what keeps the
tier correct without each caller remembering to recalculate it.

```mermaid
flowchart TB
    Earn["Earn points"]
    Burn["Burn points"]
    Adjust["Admin adjustment"]
    Redeem["Reward redeemed"]
    Challenge["Challenge completed"]

    RT["services.points.record_transaction()<br/>writes the transaction<br/>and moves total_points"]
    AT["services.tiers.apply_tier()<br/>picks the tier for the new balance"]

    Earn --> RT
    Burn --> RT
    Adjust --> RT
    Redeem --> RT
    Challenge --> RT
    RT --> AT
```

Earning applies the member's tier multiplier, so the points credited can be more
than the points asked for. Tiers are picked automatically when the balance
crosses `minPoints`.

Completing a challenge is the one action that can pay out twice: `rewardPoints`
become an `earn` transaction, and `rewardId`, if set, becomes a redemption with
source `assigned`. Progress reaching `targetValue` completes a challenge on its
own, and `POST /complete` forces it regardless of progress or deadline.

## API reference

`/health` is open. Everything below needs the bearer token.

**Members**

| Method | Path | Description |
|---|---|---|
| `POST` `GET` | `/members` | Create, list and search members |
| `GET` | `/members/count` | Member count |
| `GET` | `/members/stats` | Dashboard stats: points in circulation, tier spread |
| `GET` `PATCH` `DELETE` | `/members/{id}` | Get, update, delete a member |
| `POST` `GET` `GET` `PATCH` `DELETE` | `/member-attributes` | Custom field definitions |

**Points**

| Method | Path | Description |
|---|---|---|
| `GET` | `/members/{id}/balance` | Current balance |
| `POST` | `/members/{id}/points/earn` | Earn points, `{"points": 100}` |
| `POST` | `/members/{id}/points/burn` | Spend points, `{"points": 30}` |
| `POST` | `/members/{id}/points/adjust` | Admin adjustment, signed |
| `GET` | `/members/{id}/transactions` | Transaction history |

**Rewards, redemptions and prizes**

| Method | Path | Description |
|---|---|---|
| `POST` `GET` | `/rewards` | Create, list rewards |
| `GET` `PATCH` `DELETE` | `/rewards/{id}` | Get, update, delete a reward |
| `POST` | `/members/{id}/redeem/{rewardId}` | Redeem, debits the points cost |
| `POST` | `/members/{id}/prizes/{rewardId}` | Grant for free, no points debited |
| `GET` | `/members/{id}/prizes` | History, filter with `?source=redeemed\|assigned` |
| `GET` | `/members/{id}/redemptions` | Redemption history |

**Challenges**

| Method | Path | Description |
|---|---|---|
| `POST` `GET` | `/challenges` | Create, list challenges |
| `GET` `PATCH` `DELETE` | `/challenges/{id}` | Get, update, delete a challenge |
| `POST` `DELETE` | `/members/{id}/challenges/{challengeId}` | Assign to, remove from a member |
| `GET` | `/members/{id}/challenges` | A member's challenges, filter with `?status=` |
| `GET` | `/members/{id}/challenges/{challengeId}` | Definition plus that member's progress |
| `POST` | `/members/{id}/challenges/{challengeId}/progress` | Add progress, `{"amount": 1}` |
| `POST` | `/members/{id}/challenges/{challengeId}/complete` | Force complete and pay out |
| `POST` | `/challenges/{id}/assign-segment` | Assign to a whole segment, `{"segmentId": "..."}` |

**Products and purchases**

| Method | Path | Description |
|---|---|---|
| `POST` `GET` | `/products` | Create, list products |
| `GET` `PATCH` `DELETE` | `/products/{id}` | Get, update, delete a product |
| `POST` `GET` | `/members/{id}/purchases` | Record a purchase, list history |
| `GET` | `/members/{id}/purchase-stats` | Spend stats, `?days=` sets the window |

**Segments and tiers**

| Method | Path | Description |
|---|---|---|
| `POST` `GET` | `/segments` | Create, list segments |
| `GET` `PATCH` `DELETE` | `/segments/{id}` | Get, update, delete a segment |
| `POST` | `/segments/{id}/assign` | Add members in bulk, `{"memberIds": [...]}` |
| `POST` `GET` | `/tiers` | Create, list tiers |
| `GET` `PATCH` `DELETE` | `/tiers/{id}` | Get, update, delete a tier |

**Email and member sign in**

| Method | Path | Description |
|---|---|---|
| `POST` | `/doi/trigger` | Send a verification email |
| `POST` | `/doi/verify` | Confirm a verification code |
| `POST` | `/auth/signup` | Create a member and mail a login code |
| `POST` | `/auth/login` | Mail a login code to an existing member |
| `POST` | `/auth/verify` | Exchange the code for the member record |

### Member object

```json
{
  "id": "b3f1...",
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "phone": "+155501",
  "segments": [
    { "id": "a1c2...", "name": "vip", "description": null, "color": null }
  ],
  "pointsBalance": 70,
  "emailVerifiedAt": null,
  "isEmailVerified": false
}
```

Members join segments by id. `MemberCreate` and `MemberUpdate` take
`segmentIds: [UUID]`, picked from the segment list rather than typed free.

## DOI email verification

`/doi/trigger` takes a `type` that decides which email the member gets:

| `type` | Email | What the member does |
|---|---|---|
| `code` (default) | A 6 digit code | Types it back into the screen that started the flow, which posts to `/doi/verify` |
| `link` | A **Verify my email** button pointing at `{CLIENT_BASE_URL}/verify?memberId=<id>&code=<code>` | Presses the button, and that page posts to `/doi/verify` for them |

Both issue the same kind of single use code, good for 10 minutes and 5 attempts,
and both finish at `POST /doi/verify`. The link flow only spares the typing.
`type` is optional, so callers written before it keep working.

A `type: "link"` trigger without `CLIENT_BASE_URL` set answers `500` rather than
mailing a button that goes nowhere. The `code` flow never reads it.

**Idempotency.** While a code is live, `/doi/trigger` answers `200` and sends
nothing. The request is already satisfied by the code sitting in the member's
inbox, and a second email would quietly invalidate the first. A new code is
issued once the old one expires, is verified, or is burned through 5 wrong
guesses. Nothing is written unless the email was accepted, so a failed send does
not block the next attempt.

Asking for the *other* `type` while a code is live does issue a new one. The live
code went out in a shape this caller is not asking for, and only its hash is
stored, so the link behind it cannot be rebuilt.

**Failures.** `DOI_FROM_EMAIL` must sit on a domain verified in Resend. Until it
does, every send is rejected and `/doi/trigger` answers `500` quoting the
provider, for example `Resend 403 validation_error: The <domain> domain is not
verified`. Rate limits, provider outages and network failures answer `502`
instead, since those are worth retrying.

## Example requests

```bash
TOKEN=your-api-token

# Create a segment
curl -X POST http://localhost:8000/segments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"vip","description":"Top spending members"}'

# Create a member in that segment
curl -X POST http://localhost:8000/members \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Ada Lovelace","email":"ada@example.com","segmentIds":["<segment-id>"]}'

# Earn points
curl -X POST http://localhost:8000/members/<member-id>/points/earn \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"points":100}'

# Move a member along a challenge
curl -X POST http://localhost:8000/members/<member-id>/challenges/<challenge-id>/progress \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":1,"description":"Scanned a receipt"}'
```

## Testing

There is no pytest suite. `tests/` holds standalone regression scripts for past
production incidents, each runnable on its own:

```bash
./venv/bin/python -m tests.test_database_pool          # NullPool must be in use
./venv/bin/python -m tests.test_database_pooler_port   # session pooler is rewritten to transaction pooler
./venv/bin/python -m tests.test_doi_email_errors       # send failures are classified, not swallowed
./venv/bin/python -m tests.test_doi_trigger_flow       # /doi/trigger is idempotent while a code is live
./venv/bin/python -m tests.test_doi_link_flow          # type="link" mails a working /verify link
./venv/bin/python -m tests.test_database_url           # DATABASE_URL driver normalization
```

`test_database_url.py` fails with an `ImportError`. It imports a
`_normalize_database_url` helper that does not exist in `app/core/database.py`,
and did not exist in the old flat `database.py` either. It is left failing rather
than quietly patched over.
