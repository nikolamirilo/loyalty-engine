# Loyalty Engine

A simple loyalty API built with **FastAPI** and **Supabase** (Postgres) via
SQLAlchemy. All API routes are protected by a bearer token.

> Tables are created automatically on first run via SQLAlchemy `create_all`.
> `DATABASE_URL` is required - the app will not start without it.

## Features

- **Members** - full name, email, phone, segment memberships and a points balance.
- **Segments** - named member cohorts (e.g. "VIP", "Newsletter") with a description; members belong to any number of segments, picked from the segments list.
- **Points** - earn, burn (spend) and admin adjustments, with a full transaction history.
- **Rewards** - a catalog of redeemable rewards with optional stock limits.
- **Redemptions** - members redeem rewards by spending points.
- **Challenges** - can be bulk-assigned to every member of a segment.
- **Tiers** - optional point thresholds that apply an earn-rate multiplier.
- **Bearer token auth** - every API route requires `Authorization: Bearer <token>`.

## Project layout

Layered by responsibility: **routers** only translate HTTP <-> ORM (validate the
request via `schemas`, call a `service` for anything beyond a plain CRUD
read/write, shape the response); **services** hold the business logic that's
shared across routers or too involved for a route function; **models** are the
SQLAlchemy ORM classes; **schemas** are the Pydantic request/response shapes. A
router never imports another router - shared logic (e.g. `apply_tier`, called
from points/redemptions/challenges/members) lives in `app/services` instead.

```
loyalty-engine/
├── main.py                       # Thin compat shim: `from app.main import app`
├── requirements.txt
├── .env.example                  # Sample environment config
├── supabase/migrations/          # Hand-written SQL migrations (no Alembic - see below)
├── tests/                        # Standalone regression scripts (see Testing below)
└── app/
    ├── main.py                   # App entry point: creates the FastAPI app, wires routers
    ├── core/
    │   ├── config.py             # Settings - the only place env vars are read
    │   ├── database.py           # SQLAlchemy engine + session + Base + get_db
    │   └── security.py           # Bearer token dependency
    ├── models/                   # SQLAlchemy ORM models, one module per resource
    │   ├── enums.py
    │   ├── member.py             # Member, MemberSegment
    │   ├── member_attribute.py   # Admin-defined custom fields on members
    │   ├── segment.py
    │   ├── tier.py
    │   ├── points.py             # PointsTransaction
    │   ├── reward.py
    │   ├── redemption.py
    │   └── challenge.py          # Challenge, ChallengeAssignment, ChallengeSegmentAssignment
    ├── schemas/                  # Pydantic request/response schemas, mirrored 1:1 with models/
    ├── services/                 # Business logic shared across routers
    │   ├── tiers.py              # apply_tier - re-applied on every balance change
    │   ├── points.py             # record_transaction - the one path that mutates total_points
    │   ├── rewards.py            # availability checks + prize granting
    │   ├── segments.py
    │   ├── challenges.py         # expiry, segment fan-out, completion rewards
    │   └── custom_attributes.py  # type validation for member custom attributes
    └── routers/
        ├── members.py            # CRUD for members
        ├── member_attributes.py  # CRUD for member custom-attribute definitions
        ├── points.py             # earn / burn / adjust / transactions / balance
        ├── rewards.py            # CRUD for rewards
        ├── redemptions.py        # redeem a reward + history
        ├── challenges.py         # CRUD for challenges + member/segment assignment
        ├── segments.py           # CRUD for segments
        └── tiers.py              # CRUD for tiers
```

## Setup

```bash
# 1. (Recommended) create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env        # then set DATABASE_URL + API_TOKEN (see below)
```

### Connecting to Supabase

1. In the Supabase dashboard, go to **Project Settings → Database → Connection string**.
2. Copy the **Connection pooling** URI (Transaction mode, port `6543`) - recommended for apps.
3. Replace `[YOUR-PASSWORD]` with your database password and paste it into `.env` as `DATABASE_URL`.

```
DATABASE_URL=postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
```

Use **Transaction mode (port `6543`)**, not Session mode (`5432`). Session mode gives
each client its own Postgres backend out of a budget of ~15, which a serverless
deployment exhausts almost immediately:

```
FATAL: (EMAXCONNSESSION) max clients reached in session mode - max clients are limited to pool_size: 15
```

A session-mode Supabase pooler URL is redirected to port `6543` at startup with a
warning in the logs (`app/core/database.py`), but fix `DATABASE_URL` rather than
relying on that. If the database is unreachable anyway, the API answers `503` with
a JSON body instead of crashing the request.

SSL is enabled automatically. Tables are created on first run - no SQL migration step needed
(the DOI feature's `members.email_verified_at` column is the one exception - see
`supabase/migrations/20260820095328_doi_email_verification.sql`, which must be run
by hand since `create_all` never alters an existing table).

### DOI email verification

Sending verification codes (`/doi/trigger`) uses [Resend](https://resend.com).
Set:

```
RESEND_API_KEY=<your Resend API key>
DOI_FROM_EMAIL=<a verified Resend sender address>
```

`DOI_FROM_EMAIL` must be on a domain you have verified in Resend. Until it is,
Resend rejects every send and `/doi/trigger` answers `500` quoting the provider's
reason (e.g. `Resend 403 validation_error: The <domain> domain is not verified`);
the same reason is written to the logs. Rate limits, provider outages and network
failures answer `502` instead, since those are worth retrying.

`/doi/trigger` is idempotent while a code is live. If the member's previous code
hasn't expired (10 minutes) or been used up yet, the endpoint answers `200` with
the same body and sends nothing - the request is already satisfied by the code
sitting in their inbox, and a second email would silently invalidate the first.
A new code is issued once the old one expires, is verified, or is burned through
5 wrong guesses. Nothing is written to the database unless the email was
accepted, so a failed send can't suppress the next attempt.

## Running

```bash
uvicorn app.main:app --reload
```

(`uvicorn main:app --reload` also still works - `api/main.py` is a thin
`from app.main import app` shim kept for any external process that points at
it directly.)

- API base URL: `http://localhost:8000`
- Interactive docs (Swagger UI): `http://localhost:8000/docs` - click **Authorize**
  and paste your token to try endpoints from the browser.
- Tables are created automatically in your Supabase database on first run.

## Authentication

Every route except `/health` and the docs requires a bearer token:

```
Authorization: Bearer <API_TOKEN>
```

The token is read from the `API_TOKEN` environment variable (or `.env`) and
defaults to `dev-secret-token` for local development. Requests with a missing or
invalid token receive `401`/`403`.

## JSON casing

Every response is camelCase (`pointsBalance`, `createdAt`, `isActive`, ...), via
a shared `CamelModel` base (`app/schemas/base.py`) that generates aliases from
the snake_case Python/ORM field names - see that file for details. Request
bodies accept snake_case *or* camelCase keys, so existing snake_case payloads
keep working.

## API reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check (no auth) |
| `POST` / `GET` | `/members` | Create / list members |
| `GET` / `PATCH` / `DELETE` | `/members/{id}` | Get / update / delete a member |
| `GET` | `/members/{id}/balance` | Current points balance |
| `POST` | `/members/{id}/points/earn` | Earn points - `{"points": 100}` |
| `POST` | `/members/{id}/points/burn` | Burn (spend) points - `{"points": 30}` |
| `POST` | `/members/{id}/points/adjust` | Admin adjustment (+/-) |
| `GET` | `/members/{id}/transactions` | Points transaction history |
| `POST` / `GET` | `/rewards` | Create / list rewards |
| `GET` / `PATCH` / `DELETE` | `/rewards/{id}` | Get / update / delete a reward |
| `POST` | `/members/{id}/redeem/{reward_id}` | Redeem a reward |
| `GET` | `/members/{id}/redemptions` | Redemption history |
| `POST` / `GET` | `/tiers` | Create / list tiers |
| `GET` / `DELETE` | `/tiers/{id}` | Get / delete a tier |
| `POST` / `GET` | `/segments` | Create / list segments |
| `GET` / `PATCH` / `DELETE` | `/segments/{id}` | Get / update / delete a segment |
| `POST` | `/challenges/{id}/assign-segment` | Assign a challenge to every member of a segment - `{"segment_id": "..."}` |
| `POST` | `/doi/trigger` | Send a DOI email verification code - `{"email": "..."}` or `{"member_id": "..."}` |
| `POST` | `/doi/verify` | Confirm a DOI code - add `"code": "123456"` to the same identifier |

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

### Segment object

Members are assigned to segments by id (`MemberCreate`/`MemberUpdate` take `segment_ids: [UUID]`) - pick from the existing list rather than typing free text.

```json
{
  "id": "a1c2...",
  "name": "vip",
  "description": "Top-spending members",
  "color": "#f59e0b",
  "createdAt": "2026-01-01T00:00:00Z",
  "memberCount": 12
}
```

## Example requests

```bash
TOKEN=dev-secret-token

# Create a segment
curl -X POST http://localhost:8000/segments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"vip","description":"Top-spending members"}'

# Create a member in that segment (segment_ids from the response above)
curl -X POST http://localhost:8000/members \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Ada Lovelace","email":"ada@example.com","phone":"+155501","segment_ids":["<segment-id>"]}'

# Earn points
curl -X POST http://localhost:8000/members/1/points/earn \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"points":100}'

# Burn points
curl -X POST http://localhost:8000/members/1/points/burn \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"points":30}'

# Get member data
curl http://localhost:8000/members/1 -H "Authorization: Bearer $TOKEN"
```

## Notes

- Earning points applies the member's tier multiplier (if any tiers are defined);
  tiers are assigned automatically based on the balance crossing `min_points`.
- This app uses SQLAlchemy `create_all` for *new* tables, which is fine for
  greenfield tables but never alters existing ones. Schema changes to existing
  tables (new/dropped/retyped columns) need a hand-written SQL script run
  against Supabase first - see `supabase/migrations/`. After that, `create_all`
  picks up any brand-new tables on the next app start.

## Testing

There's no pytest suite yet - `tests/` holds standalone regression scripts for
past production incidents, each runnable directly:

```bash
./venv/bin/python -m tests.test_database_pool          # NullPool must be in use
./venv/bin/python -m tests.test_database_pooler_port   # session pooler -> transaction pooler
./venv/bin/python -m tests.test_doi_email_errors       # DOI send failures are classified, not swallowed
./venv/bin/python -m tests.test_doi_trigger_flow       # /doi/trigger is idempotent while a code is live
./venv/bin/python -m tests.test_database_url           # DATABASE_URL driver normalization
```

`test_database_url.py` currently fails with an `ImportError` - it imports a
`_normalize_database_url` helper that doesn't exist in `app/core/database.py`.
This predates the `app/` restructure (the old flat `database.py` didn't have it
either); it's left failing rather than silently patched over.
