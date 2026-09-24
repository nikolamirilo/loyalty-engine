# Database

The loyalty engine stores everything in one Supabase Postgres database. This
folder holds the SQL migrations. Only the [API](../api) connects to the database,
so this is the only place schema changes are written by hand.

## Why migrations exist at all

The API creates tables on startup with SQLAlchemy `create_all`. That helper has
one hard limit worth remembering:

> `create_all` creates tables that do not exist yet. It never alters a table that
> does exist.

So the split is:

| Change | How it happens |
|---|---|
| A brand new table | Automatic. Start the API and it appears. |
| A new column, a dropped column, a changed type, an index, an enum value | Manual. Write SQL here and run it against Supabase first. |

Run the SQL before deploying the code that depends on it. Otherwise the API
starts against a table that is missing the column it expects.

## Applying a migration

Either paste the file into the Supabase SQL editor, or use the Supabase CLI if
the project is linked:

```bash
supabase db push          # apply local migrations to the linked project
supabase db pull          # pull the live schema back into a new migration file
```

`20260921104524_remote_schema.sql` is a full snapshot produced by `db pull`. It
replaced the older per feature migration files. Migrations after it add one
feature each, such as `20260924090000_member_events.sql` for events and rules.

## What the schema looks like

```mermaid
erDiagram
    tiers            ||--o{ members : ranks
    members          ||--o{ member_segments : "belongs to"
    segments         ||--o{ member_segments : groups
    members          ||--o{ points_transactions : "point history"
    members          ||--o{ redemptions : received
    rewards          ||--o{ redemptions : "given as"
    members          ||--o{ purchases : made
    products         ||--o{ purchases : "sold as"
    members          ||--o{ challenge_assignments : "works on"
    challenges       ||--o{ challenge_assignments : "handed out as"
    challenges       ||--o{ challenge_segment_assignments : "pushed to"
    segments         ||--o{ challenge_segment_assignments : receives
    rewards          ||--o{ challenges : "pays out"
    members          ||--o{ email_verification_codes : "DOI codes"
    members          ||--o{ member_login_codes : "login codes"
    event_types      ||--o{ event_rules : "decided by"
    members          ||--o{ member_events : "did"
    event_types      |o--o{ member_events : "recorded as"
    event_rules      ||--o{ event_rule_runs : "counted in"
```

Twenty-one tables in total. Three are not drawn above: `programs`, which owns
nearly every other row, `member_identities`, the person behind each membership,
and `member_attributes`, which holds admin defined custom field definitions
while the values themselves live in a JSON column on `members`.

Deleting a member clears their segments, transactions, redemptions, purchases,
challenge assignments, events and codes along with them. Deleting an event type
deletes its rules but keeps members' events, which remember the type's key. Deleting a reward or a product
is gentler: challenges keep working with `reward_id` set to null, and purchases
keep the product name they recorded at the time.

## Enums

| Type | Values |
|---|---|
| `transactiontype` | `earn`, `spend`, `adjust` |
| `redemptionsource` | `redeemed`, `assigned` |
| `challengestatus` | `assigned`, `in_progress`, `completed`, `expired`, `cancelled` |
| `doitype` | `code`, `link` |

Adding a value to one of these is a schema change, so it needs a migration here.

## Connection notes

Use the **transaction pooler** on port `6543`, not the session pooler on `5432`.
Session mode gives every client its own Postgres backend out of a budget of about
15, which a serverless deployment burns through almost at once. The API rewrites a
session mode URL to `6543` at startup and logs a warning, but fix the
`DATABASE_URL` rather than leaning on that. See [api/README.md](../api/README.md)
for the full setup.
