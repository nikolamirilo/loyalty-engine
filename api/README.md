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

```
loyalty-engine/
├── main.py            # App entry point, DB init, auth wiring
├── auth.py            # Bearer token dependency
├── database.py        # SQLAlchemy engine (Supabase/Postgres) + session + Base
├── models.py          # SQLAlchemy ORM models
├── schemas.py         # Pydantic request/response schemas
├── requirements.txt
├── .env.example       # Sample environment config
├── migrations/        # Hand-written SQL migrations (no Alembic - see below)
└── routers/
    ├── members.py     # CRUD for members
    ├── points.py      # earn / burn / adjust / transactions / balance
    ├── rewards.py     # CRUD for rewards
    ├── redemptions.py # redeem a reward + history
    ├── challenges.py  # CRUD for challenges + member/segment assignment
    ├── segments.py    # CRUD for segments
    └── tiers.py       # CRUD for tiers
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

SSL is enabled automatically. Tables are created on first run - no SQL migration step needed.

## Running

```bash
uvicorn main:app --reload
```

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
  "pointsBalance": 70
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
  "created_at": "2026-01-01T00:00:00Z",
  "member_count": 12
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
  against Supabase first - see `migrations/`. After that, `create_all` picks up
  any brand-new tables on the next app start.
