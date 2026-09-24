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
| **Tiers** | Conditions - points balance, lifetime purchase spend/count, segments, custom attributes, ANDed together - that apply an earn rate multiplier, assigned automatically whenever any of them changes. |
| **Rewards** | The redeemable catalog, with optional stock limits. |
| **Redemptions and prizes** | Members spend points on a reward, or staff grant one for free. |
| **Challenges** | Goals with a target value. Progress accrues, and completion pays out points, a reward, or both. Can be pushed to a whole segment at once. |
| **Products and purchases** | A catalog members buy from on unlimited credit. Purchases are a spend signal, not a points transaction. |
| **Events and rules** | Admin defined event types with typed attributes. `POST /events` records one for a member and runs every matching rule: add points, grant a reward, move a challenge, add to a segment, or update member fields. |
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
    │   ├── tiers.py              # apply_tier, re-run whenever a tier's conditions can shift
    │   ├── points.py             # record_transaction, the only path that moves total_points
    │   ├── rewards.py            # availability checks and prize granting
    │   ├── challenges.py         # expiry, segment fan out, progress, completion rewards
    │   ├── events.py             # track_event: records an event and runs its rules
    │   ├── rules/                # the rule engine: fields, conditions, one handler per effect
    │   ├── products.py           # purchase recording and spend stats
    │   ├── member_auth.py        # passwordless member login codes
    │   ├── email_verification.py # DOI codes and links
    │   ├── email_sending.py      # Resend transport
    │   ├── segments.py
    │   └── custom_attributes.py  # type validation for member custom attributes
    └── routers/                  # members, member_attributes, points, rewards,
                                  # redemptions, products, purchases, challenges,
                                  # segments, tiers, event_types, events, doi, auth
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

## How tiers stay in sync

A tier's conditions (`app/services/rules/fields.py:tier_fields`) can test the
points balance, lifetime purchase spend and count, segments, and custom
attributes - all of them, ANDed together, the same "if" language event rules
use. Every path that can move one of those calls `apply_tier` (or its batched
sibling `reapply_tiers`), so the member's stored tier never goes stale:

```mermaid
flowchart TB
    Earn["Earn / burn / adjust points"]
    Redeem["Reward redeemed"]
    Challenge["Challenge completed"]
    Purchase["Purchase recorded"]
    Segment["Segment membership changed"]
    Attr["Custom attributes changed"]
    TierEdit["A tier is created, edited or deleted"]

    AT["services.tiers.apply_tier() / reapply_tiers()<br/>tries every tier highest rank first,<br/>assigns the first whose conditions all match"]

    Earn --> AT
    Redeem --> AT
    Challenge --> AT
    Purchase --> AT
    Segment --> AT
    Attr --> AT
    TierEdit -->|"re-checks every member<br/>in the program"| AT
```

Earning applies the member's tier multiplier, so the points credited can be
more than the points asked for. Tiers are tried from the highest `rank` down;
a member is assigned to the first tier whose conditions all match, or to none
if no tier's do. A tier with no conditions matches everyone, so one with the
lowest rank acts as a catch-all default.

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

**Events and rules**

| Method | Path | Description |
|---|---|---|
| `POST` `GET` | `/event-types` | Define, list event types, each with its rules |
| `GET` `PATCH` `DELETE` | `/event-types/{id}` | Get, update, delete an event type |
| `GET` `POST` | `/event-types/{id}/rules` | List, create rules |
| `PATCH` `DELETE` | `/event-types/{id}/rules/{ruleId}` | Update, delete a rule |
| `POST` | `/events` | Record an event and run its rules, see [Events and rules](#events-and-rules) |
| `GET` | `/events` | Every event in the program, newest first, with its member. `?type=<key>` filters by event type |
| `GET` | `/members/{id}/events` | A member's events, with what their rules did |

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

## Events and rules

An event type is something a member does that another system reports, such as
"Order placed". Define it first with the attributes it carries. Its `key`,
derived from the name (`orderPlaced`), is what callers send as `type`, and it
never changes. Unknown types and attributes are rejected, so a typo in an
integration fails loudly instead of earning nothing.

A rule reads as one sentence: when the event arrives, if all conditions hold,
run all effects. There is no OR; two rules express one. Every matching rule
runs, and all of them see the member as they were when the event arrived, so
rule order never changes the outcome.

```json
{
  "name": "Points for the order total, first order sets the store",
  "conditions": [{ "field": "event.attributes.amount", "operator": "gte", "value": 20 }],
  "effects": [
    { "type": "addPoints", "fromAttribute": "amount" },
    { "type": "updateMember", "fields": [
      { "field": "member.customAttributes.favouriteStore", "fromAttribute": "store" },
      { "field": "member.phone", "value": null }
    ] }
  ],
  "limitPerMember": null
}
```

| A condition can test | Path |
|---|---|
| An event attribute | `event.attributes.<key>` |
| The points balance | `member.pointsBalance` |
| The tier, by id | `member.tier` |
| Segments, by id, with `contains` | `member.segments` |
| A custom attribute | `member.customAttributes.<key>` |

Operators are `eq`, `neq`, `gt`, `gte`, `lt`, `lte` and `contains`, limited to
the ones that fit the field's type.

| Effect | What it does |
|---|---|
| `addPoints` | Earns a fixed number of `points`, or the value of the number attribute named in `fromAttribute`. The tier multiplier applies, as on `/points/earn`. |
| `burnPoints` | Spends `points` or `fromAttribute`, the same way. Like `/points/burn` it never goes below zero: a member without enough points is skipped. |
| `grantReward` | Grants `rewardId` for free, if it is active and in stock. |
| `assignChallenge` | Starts `challengeId` for the member, if it is active and they don't have it yet. |
| `addChallengeProgress` | Adds a fixed `amount` (default 1), or the value of the number attribute named in `fromAttribute`, to `challengeId`, for members who have that challenge. |
| `addToSegment` | Adds the member to `segmentId`, which also hands them that segment's challenges. |
| `removeFromSegment` | Takes the member out of `segmentId`. Challenges it handed them are kept. |
| `updateMember` | Sets one or more of `member.name`, `member.phone` and `member.customAttributes.<key>`, each to a fixed `value` (null clears it) or to the event attribute named in `fromAttribute`. Email can't be set by a rule. |

Points earned or burned by a rule show in the member's transactions as
`Effect of event <event name>`.

A rule is checked when it is saved, so a missing reward or an attribute of the
wrong type is a `400` then rather than a silent miss later. An effect whose
target has gone since, such as a deleted reward or a challenge the member
doesn't have, is skipped and the event records why. `limitPerMember` caps how
often one member can trigger a rule; `1` means the first time only.

**Retries.** Send your own `eventId` to make retries safe: the same id for the
same member returns the first result with `200` and runs nothing again.

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

# Send an event; the response lists what its rules did
curl -X POST http://localhost:8000/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"memberId":"<member-id>","type":"orderPlaced","attributes":{"amount":45},"eventId":"order-1001"}'
```

## Testing

Two kinds of tests live under `tests/`.

### The flow suite

`tests/integration/` is a pytest suite that drives one member and one reward
through the routes a real client uses: create the member, read it, update it,
check the balance, earn, burn, create a reward, grant it as a prize, redeem it,
then delete both. A second file does the same for events: define an event
type and its rules, send events, and check what the rules did. It runs against
a real Postgres, not a mock, so constraints and cascades are exercised too.

These tests write and delete rows, so they refuse to start unless
`TEST_DATABASE_URL` is set. They never fall back to `DATABASE_URL`, which means
a stray `.env` cannot point them at anything you care about.

```bash
pip install -r requirements.txt -r requirements-dev.txt

# Any throwaway Postgres. sslmode=disable because a local one serves no TLS.
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/loyalty_test?sslmode=disable"
pytest
```

Tables are created on connect, so an empty database is all you need.

Every request is timed, and the run ends with a table of route, status and
latency:

```
Step           Method  Route                      Status  Latency  Result
-------------  ------  -------------------------  ------  -------  ------
create_member  POST    /members                      201  35.8 ms  ok
get_member     GET     /members/{id}                 200  12.4 ms  ok
earn_points    POST    /members/{id}/points/earn     201  22.4 ms  ok
...
```

That is server side handling time: routing, auth, the handler and the database
round trip. The app is called in process, so no network transfer is included,
which is the point. Localhost network time would only add noise.

In CI the same table is written to the GitHub Actions run summary, so you can
read it without opening the log. The workflow is
[`.github/workflows/api-tests.yml`](../.github/workflows/api-tests.yml), which
starts a Postgres service container and runs the suite on any push or pull
request touching `api/`.

### Incident regression scripts

The scripts directly under `tests/` are standalone programs guarding against
past production incidents, each runnable on its own. They are not pytest tests,
which is why `pytest.ini` points `testpaths` at `tests/integration` only:

```bash
./venv/bin/python -m tests.test_database_pool          # NullPool must be in use
./venv/bin/python -m tests.test_database_pooler_port   # session pooler is rewritten to transaction pooler
./venv/bin/python -m tests.test_doi_email_errors       # send failures are classified, not swallowed
./venv/bin/python -m tests.test_doi_trigger_flow       # /doi/trigger is idempotent while a code is live
./venv/bin/python -m tests.test_doi_link_flow          # type="link" mails a working /verify link
./venv/bin/python -m tests.test_event_rules            # every rule effect, limits, retries, save-time checks
./venv/bin/python -m tests.test_database_url           # DATABASE_URL driver normalization
```

`test_database_url.py` fails with an `ImportError`. It imports a
`_normalize_database_url` helper that does not exist in `app/core/database.py`,
and did not exist in the old flat `database.py` either. It is left failing rather
than quietly patched over.
