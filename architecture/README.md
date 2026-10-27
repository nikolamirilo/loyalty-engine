# Loyalty Engine: Technical Architecture

| | |
|---|---|
| **Repository** | `nikolamirilo/loyalty-engine` |
| **Services** | Loyalty API (FastAPI), Client (Next.js), MCP server (FastMCP) |
| **Hosting** | Vercel, region `dub1` (Dublin). Database on Supabase, `eu-west-1` (Ireland) |
| **Diagram source** | [`make_diagram.py`](make_diagram.py) writes [`architecture.svg`](architecture.svg); [`render_png.js`](render_png.js) renders [`architecture.png`](architecture.png) with Playwright |

![Loyalty Engine system architecture](architecture.png)

## 1. Summary

Loyalty Engine is a loyalty program platform. Members earn and spend points,
move up tiers, complete challenges and redeem rewards. Staff run one or more
**programs** from an admin console. Members use a member app. AI agents work
on the same data through an MCP server.

There are three deployable services and one database:

| Service | Tech | What it does |
|---|---|---|
| **Loyalty API** (`api/`) | Python 3.11, FastAPI, SQLAlchemy 2, Pydantic 2 | Holds all business logic. It is the only service with a database connection. |
| **Client** (`client/`) | Next.js 16, React 19, SWR, Tailwind 4 | Runs the admin console at `/admin`, the member app at `/`, and the user docs at `/docs`. |
| **MCP server** (`mcp-server/`) | Python, FastMCP (Streamable HTTP) | Offers the API to AI agents as 78 MCP tools. |
| **Database** (`supabase/`) | Supabase Postgres + Storage | 21 tables, plus a public bucket for program logos. |

The main rule is that **only the API talks to the database**. The client and
the MCP server call the API over HTTPS with a bearer token, so every business
rule lives in one place.

## 2. Components

### 2.1 Loyalty API

The API code is split into layers. A router never imports another router.
Shared logic goes in `services/`.

| Layer | Folder | Job |
|---|---|---|
| Core | `app/core/` | Config (the only place that reads env vars), DB engine and session, auth, program resolution, domain errors, monitoring |
| Routers | `app/routers/` | Turn HTTP into ORM calls and back. Plain CRUD can use models directly. |
| Services | `app/services/` | Business logic: points ledger, tiers, rule engine, challenges, rewards, DOI, member login. Services never import FastAPI. |
| Integrations | `app/integrations/` | One module per outside provider: `email.py` (Resend) and `storage.py` (Supabase Storage). |
| Models / Schemas | `app/models/`, `app/schemas/` | SQLAlchemy ORM classes and Pydantic shapes, kept one to one. |

Key design points:

- **camelCase JSON.** Every response uses camelCase. It comes from a shared
  `CamelModel` in `app/schemas/base.py`. Requests accept either casing.
- **Points ledger.** Every balance change goes through
  `services/points.record_transaction`. It writes the ledger row, updates the
  stored `total_points` and re-applies the tier in a single step, so these
  three can never drift apart.
- **Tiers stay in sync.** Anything that can change a tier condition calls
  `apply_tier` or `reapply_tiers`: points, purchases, segments, custom
  attributes, completed challenges, and tier edits.
- **Rule engine.** `POST /events` records an event and runs every matching
  rule. All rules see the member as they were when the event arrived. Effects
  are `addPoints`, `burnPoints`, `grantReward`, `assignChallenge`,
  `addChallengeProgress`, `addToSegment`, `removeFromSegment` and
  `updateMember`.
- **Concurrency.** Writes that read and then change a balance, stock or
  progress lock the row first with `SELECT ... FOR UPDATE`. This covers points,
  redemptions, rewards, challenges, events and rule effects.
- **Idempotent events.** A caller can send its own `eventId`. If the same
  `eventId`, member and type arrive again, the API returns the first result
  with `200` and runs nothing again.

### 2.2 Client (Next.js)

One Next.js project serves two separate apps. They share components but never
share a session.

| Path | Who | Guard |
|---|---|---|
| `/admin/**` | Staff | `admin_session` cookie, valid for 7 days |
| `/home`, `/products`, `/wallet`, `/account` | Members | `member_session` cookie, valid for 30 days |
| `/`, `/login`, `/verify`, `/p/<slug>/claim`, `/docs` | Public | none |

The browser never calls the API and never touches the database. Requests reach
the API in three ways, all through the Next.js server:

1. **First paint.** Server Components call `lib/api.ts`, a typed client that
   retries and unwraps errors.
2. **Writes.** Server Actions call the API, then call `revalidatePath` to clear
   the router cache.
3. **Live reads.** The browser uses SWR on `/api/le/<path>`, a same-origin
   proxy. It checks the admin session, then forwards the request with the
   token.

`lib/server/upstream.ts` imports `server-only`. If it is imported from a
Client Component, the build fails, so the API token can't leak into the
browser bundle. The client has no `NEXT_PUBLIC_*` variables.

### 2.3 MCP server

- **Transport.** Streamable HTTP at `/mcp`, in `stateless_http` mode so any
  serverless instance can handle any request.
- **Two tokens, on purpose.** Callers authenticate with a token from
  `MCP_CLIENT_TOKENS`. Each token has a name and scopes (`read`, `write`,
  `admin`). The server then calls the API with its own service token. To
  revoke an agent, you edit `MCP_CLIENT_TOKENS`, and the API token never has
  to change.
- **Scope check.** Every tool calls `require_scope(...)` on its first line.
  Tools also declare `READ`, `WRITE` or `DELETE` annotations, which clients use
  to ask for confirmation.
- **Left out on purpose.** There is no `delete_program` tool, and no member
  sign-in tools.

### 2.4 Database

- **Supabase Postgres, 21 tables.** Almost every row is owned by a `programs`
  row. `member_identities` holds the person, and `members` holds that person's
  membership in one program.
- **Schema changes.** `create_all` creates new tables when the API starts. Any
  change to an existing table needs a hand-written SQL migration in
  `supabase/migrations/`. Apply it **before** you deploy the code that depends
  on it.
- **Storage.** Program logos go in the public bucket `program-assets`. Only the
  API uploads them, using the service role key.

## 3. Multi-program model

One API serves several loyalty programs. The `X-Program-Id` header picks the
program for each request. It takes a program UUID or slug, and
`app/core/program.get_program` resolves it.

| Endpoints | `X-Program-Id` |
|---|---|
| Members, points, rewards, tiers, challenges, segments, products, purchases, events | Picks the program. If it is missing, the API uses the default program and logs a warning. |
| `/programs` | Not used. This is how a caller finds the list of programs. |
| `/doi/*`, `/auth/*` | Not used. These work on the person, not a program. |
| `/prizes/claim/*` | Not used. The claim token already identifies the program. |

Every person belongs to every program. Name, email and email verification are
shared across programs. Points, tier, rewards and challenge progress are kept
separately for each program. `tests/regression/test_program_isolation.py`
checks that one program never sees another program's data.

## 4. Security

| Area | How it works |
|---|---|
| API authentication | One shared bearer token (`API_TOKEN`), compared in constant time. It is applied to every router in `app/main.py`, so a new router can't ship without auth. Only `/health` and the docs are open. |
| Staff sign-in | Username and password, compared in constant time. After 3 failed attempts, that IP is locked out for 10 minutes. The lockout is held in memory, so it resets when the process restarts. |
| Member sign-in | Passwordless. A 6-digit code is emailed. It lasts 10 minutes and allows 5 attempts. Only a hash of the code is stored. The response never reveals whether an email is registered. |
| Sessions | HMAC-signed cookies (`AUTH_SECRET`). They are `httpOnly`, and `secure` in production. `proxy.ts` checks them, and each protected layout checks them again. |
| Resend abuse | Code emails have a 60-second cooldown per person. A second request inside that window gets `429` with a `Retry-After` header. |
| MCP | Per-agent tokens and scopes. A DNS-rebinding check runs on Host and Origin, using `MCP_ALLOWED_HOSTS` and the Vercel domains. CORS is open only to `https://claude.ai`. |
| Secrets | All secrets are server-side environment variables. The Supabase service role key stays inside the API. |
| PII in monitoring | See section 6. Sentry does not collect member IPs, cookies, emails, names, phone numbers or codes. |

## 5. Error handling

### 5.1 API: one error model, one place that turns it into HTTP

Services raise **domain errors** from `app/core/errors.py`, not
`HTTPException`. This keeps them independent of HTTP, so scripts and the rule
engine can call them too. One handler in `app/main.py` turns each domain error
into a response. The body is `{"detail": "..."}`, the same shape FastAPI uses,
so a client can't tell the two apart.

| Error | Status | When |
|---|---|---|
| `InvalidInput` | 400 | The request breaks a business rule that the schema can't express. |
| `NotFound` | 404 | The resource does not exist in this program. |
| `Conflict` | 409 | The request clashes with the current state, for example an email that is already verified. |
| `PayloadTooLarge` | 413 | The logo is over 2 MB. |
| `RateLimited` | 429 | A code email was asked for inside its cooldown. The response sets `Retry-After`. |
| `Misconfigured` | 500 | The deployment is set up wrong, for example an unverified sender domain. A retry won't help; someone has to fix it. |
| `UpstreamError` | 502 | Resend or Storage failed or could not be reached. Worth retrying. |
| `FeatureUnavailable` | 503 | An optional feature is off because its settings are missing, for example Storage keys. |
| Pydantic validation | 422 | FastAPI's standard error. `detail` is a list of `{msg, loc}`. |

Infrastructure errors have their own handlers, so a client never gets a raw
traceback or an empty 500:

| Exception | Response | Why |
|---|---|---|
| `sqlalchemy.OperationalError` | **503**: "Database is temporarily unavailable" | The pooler is full or the project is paused. That isn't the caller's fault. |
| `sqlalchemy.IntegrityError` | **409**: "The request conflicts with existing data" | A constraint was hit that the route didn't check first. The error is reported, because it means the route is missing a check. |
| Error during `create_all` at startup | Logged and reported. The app still boots. | A database blip during a cold start must not take the whole function down. |

**Email failures are sorted into two kinds** in `integrations/email.py`:

- **Permanent.** Resend returns 400, 401, 402, 403, 404, 405, 409, 413 or 422,
  for example a bad key or an unverified domain. The API raises `Misconfigured`
  (500) and the message quotes the provider.
- **Transient.** Resend returns 429 or 5xx, or the network fails. The API
  raises `UpstreamError` (502).

Code emails are sent **before** anything is written to the database. If the
send fails, the previous code still works and no cooldown starts.

**Prize emails never fail the request.** The prize is already assigned. The
API returns `emailSent: false` with an `emailError`, and reports the failure to
Sentry.

### 5.2 Timeout budget

Vercel stops a function after 10 seconds. Each timeout is set to fail cleanly
before that:

| Hop | Limit | Where |
|---|---|---|
| API to Postgres (connect) | 10 s | `core/database.py` `CONNECT_TIMEOUT_SECONDS` |
| API to Resend | 10 s (the SDK default is 30 s) | `integrations/email.py` |
| Client `/api/le` proxy to API | 8 s overall deadline, then a JSON `504` | `app/api/le/[...path]/route.ts` |
| MCP server to API | 15 s, set with `LOYALTY_API_TIMEOUT_SECONDS` | `mcp-server/app/core/config.py` |

### 5.3 Client

| Layer | Behaviour |
|---|---|
| `lib/api.ts` (server) | Up to 3 attempts, with backoff of 150 ms then 300 ms. It retries **only** network errors and 502, 503 and 504. It never retries a 500, because retrying a bug only delays the error. It turns FastAPI's `detail` into an `ApiError(status, message)`. A bad `API_BASE_URL` gives a clear error. |
| `/api/le` proxy | Same retry rules, inside the 8-second deadline. If the API can't be reached it returns `502` JSON, and on timeout it returns `504` JSON. Without a session it returns `401` JSON, not an HTML redirect. |
| Server Actions | Return `ActionState { ok, error }`. An `ApiError` shows the API's own message. Any other error is logged with `console.error`, and the user sees a generic "Something went wrong". |
| SWR (browser) | `lib/swr/fetcher.ts` throws a client-safe `ApiError` with the `detail` message. Components show it in `ErrorBanner` or `Toast`. |
| Route errors | `app/error.tsx` is the error boundary. It shows the message with **Try again** and **Reload** buttons. `not-found.tsx` handles 404s. |

### 5.4 MCP server

A non-2xx response from the API raises `LoyaltyAPIError(status, detail)`. MCP
returns it to the agent as a tool error, for example `404: Member not found`.
A missing scope also becomes a tool error rather than a partial result. A bad
inbound token gets a `401` JSON response before any MCP handling runs.

### 5.5 Configuration errors fail at startup

The API and the MCP server read their environment once, in `core/config.py`.
If a required variable is missing, the service won't start, and the error says
what to set. It does not wait for the first request that needs the value. Some
mistakes are corrected with a warning instead. For example, a Supabase
**session** pooler URL on port 5432 is rewritten to the transaction pooler on
port 6543, and the API logs a warning.

## 6. Monitoring and observability

### 6.1 Sentry (API)

`app/core/monitoring.py` is the only module that imports `sentry_sdk`. If
`SENTRY_DSN` is not set, it does nothing. That is the case in tests, CI and
local runs.

**What reaches Sentry:**

| Source | How |
|---|---|
| Unhandled exceptions (any 500) | The FastAPI integration captures them. |
| 5xx domain errors (`Misconfigured`, `UpstreamError`, `FeatureUnavailable`) | The FastAPI integration captures them, together with the Resend or Storage error that caused them. |
| Errors the app handles on purpose | Sent with `report(exc)`: database unavailable (503), a constraint that wasn't checked (409), `create_all` failing at startup, a prize email that didn't go out. |
| Log records | Kept as **breadcrumbs only** (`LoggingIntegration(event_level=None)`), so the same problem is never reported twice. |

**Context on each event:**

- `environment` comes from `SENTRY_ENVIRONMENT`, or else `VERCEL_ENV`
  (`production` or `preview`), or else `development`.
- `release` comes from `SENTRY_RELEASE`, or else `VERCEL_GIT_COMMIT_SHA`, so
  every error is linked to the commit that was deployed.
- Tag `program` holds the program slug for the request, set in
  `get_program`.
- Performance traces are on. The share of requests traced comes from
  `SENTRY_TRACES_SAMPLE_RATE`, which defaults to `1.0`.

**Privacy:** `send_default_pii=False` (no IPs, cookies or query strings) and
`include_local_variables=False`. The event scrubber also masks `email`,
`name`, `phone` and `code` at any depth, on top of Sentry's default list
(tokens, passwords, the `Authorization` header).

### 6.2 Logs

- **API.** Uses the `uvicorn.error` logger, which goes to Vercel function
  logs. Notable warnings: a request that fell back to the default program, a
  session pooler URL being rewritten, and full `logger.exception` traces for
  database and email failures. Email failures include the provider's own
  reason.
- **Client.** Unexpected Server Action errors are logged with `console.error`
  and show up in Vercel logs.
- **MCP server.** Platform logs only.

### 6.3 Health checks

| Service | Endpoint | Auth |
|---|---|---|
| API | `GET /health` returns `{"status": "ok"}` | none |
| MCP server | `GET /healthz` returns `{"status": "ok"}` | none |

These can be used by an uptime monitor. Note that neither endpoint checks the
database (see section 10).

### 6.4 Synthetic monitoring from the scheduled test runs

The API test suite also runs **twice a day, at 07:00 and 13:00 UTC**. Each run
emails a report with the latency of every route (see section 7.3). This finds
regressions and slow routes even on days when nobody pushes code.

## 7. Testing and CI

### 7.1 Local pre-commit hook (Husky)

The hook in `.husky/pre-commit` runs the cheapest checks first, and only for
the parts of the repo that are staged:

| Staged files | Checks |
|---|---|
| `*.py` | Python syntax check with `ast.parse`, without importing anything |
| `client/**/*.{ts,tsx,js,jsx,mjs}` | `eslint`, then `tsc --noEmit`, then `next build` |

`git commit --no-verify` skips the hook. That is why CI runs these checks
again.

### 7.2 GitHub Actions workflows

Each workflow runs only when files in its own folder change.

| Workflow | Runs on | What it checks |
|---|---|---|
| **API tests** (`api-tests.yml`) | push or PR touching `api/**`, manual | Starts a **Postgres 16 service container**, installs the Python 3.11 dependencies and runs `pytest`. It uploads the report as an artifact (kept 14 days), then emails the report. |
| **API tests (scheduled)** (`api-tests-scheduled.yml`) | cron 07:00 and 13:00 UTC, manual | Calls the same workflow through `workflow_call`, so there is only one copy of the setup. |
| **Client checks** (`client-checks.yml`) | push or PR touching `client/**`, manual | Node 22, `npm ci`, `npm run lint`, `tsc --noEmit`. The build is left to the Vercel deploy. |
| **MCP server checks** (`mcp-server-checks.yml`) | push or PR touching `mcp-server/**`, manual | `compileall` on every module. Imports `app.server` the same way a deploy does. Fails on a bad import, a duplicate tool name, or a tool on a program-scoped route that has no `program` argument. |

### 7.3 API test suite

**Flow suite** (`api/tests/integration/`, 20 tests). It runs against a real
Postgres, not a mock, so constraints and cascades are tested too.

- `test_member_reward_flow.py`: creates a member, then reads it, updates it,
  checks the balance, earns and burns points, creates a reward, assigns it as
  a prize, redeems it, and finally deletes the member and the reward.
- `test_member_event_flow.py`: defines an event type and its rules, sends
  events, checks that a retry with the same `eventId` runs nothing, checks
  `limitPerMember`, lists events, and checks that deleting the event type keeps
  the history.

Safety: the suite **refuses to run** without `TEST_DATABASE_URL` and never
falls back to `DATABASE_URL`. It forces `SENTRY_DSN` to empty, so test runs
never send anything to Sentry.

**Latency report.** Every request is timed in-process, covering routing, auth,
the handler and the database round trip. The table is written to the GitHub
run summary, to `latency.md`, and to `latency.json`.

**Email report.** `.github/scripts/send_ci_report.py` sends the report through
Resend, the provider the app already uses:

- The subject is the alert: `✅ API tests passed`, `🔴 FAILED`, or
  `⚠️ did not run`, followed by the date and the time slot.
- The body has an HTML latency table, and failed rows are tinted red. On
  failure it also includes the last 120 lines of pytest output.
- It is sent for pushes, manual runs and scheduled runs. Pull requests are left
  out, because their result already shows as a check on the PR.
- If a fork PR has no secrets, the email step is skipped and a note goes into
  the run summary.

**Incident regression scripts** (`api/tests/regression/`, 11 scripts). These
are standalone programs that run against in-memory SQLite. Each guards against
a problem that already happened in production:

| Script | Guards against |
|---|---|
| `test_database_pool` | A pool other than NullPool being used, which caused the EMAXCONNSESSION outage |
| `test_database_pooler_port` | The session pooler URL no longer being rewritten to the transaction pooler |
| `test_doi_email_errors` | Send failures being swallowed instead of classified |
| `test_doi_trigger_flow` / `test_doi_link_flow` | Code resend, the 429 cooldown, and working `/verify` links breaking |
| `test_member_login_resend` | Login code resend and cooldown breaking |
| `test_prize_claims` | Prize emails not linking to the right program's claim page |
| `test_event_rules` | Any rule effect, limit, retry or save-time check breaking |
| `test_program_branding` | Colour validation and logo upload, replace or delete breaking |
| `test_program_isolation` | One program seeing another program's data |
| `test_tier_conditions` | Tier conditions not combining correctly or not staying in sync |

Run all of them with:
`for f in tests/regression/test_*.py; do python -m tests.regression.$(basename "$f" .py) || break; done`

### 7.4 What is not covered

- **The regression scripts are not run in CI.** `pytest.ini` limits
  `testpaths` to `tests/integration`, and no workflow calls the scripts.
- The client has **no automated tests**. It only gets lint and typecheck.
- The MCP server has no tests that call tools. It only gets the import and
  registry check.
- No Python linter or type checker runs on the API in CI.

## 8. Deployment and environments

| Item | Detail |
|---|---|
| Platform | Vercel, Git integration. Each service is its own Vercel project, rooted at `api/`, `client/` or `mcp-server/`. |
| Region | `dub1` (Dublin), pinned in `api/vercel.json` and `client/vercel.json`. This is next to the Supabase database in `eu-west-1`. Calling it from across the Atlantic added about 100 ms per query, which pushed `POST /programs` past the 10-second limit. |
| Database connections | Supabase **transaction pooler on port 6543**, with `NullPool` (each request opens one connection and closes it), `pool_pre_ping`, and `sslmode=require`. |
| Release order | 1) Apply SQL migrations in Supabase. 2) Deploy the API. 3) Deploy the client and the MCP server. |
| Preview vs production | Sentry `environment` follows `VERCEL_ENV`, so errors from preview deploys are kept apart. |

### Environment variables

| Service | Required | Optional |
|---|---|---|
| API | `DATABASE_URL`, `API_TOKEN`, `RESEND_API_KEY`, `EMAIL_FROM` | `CLIENT_BASE_URL` (DOI links, prize claim links), `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `STORAGE_BUCKET`, `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, `SENTRY_RELEASE`, `SENTRY_TRACES_SAMPLE_RATE` |
| Client | `API_TOKEN`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `AUTH_SECRET` | `API_BASE_URL` (default `http://127.0.0.1:8000`) |
| MCP server | `LOYALTY_API_BASE_URL`, `LOYALTY_API_SERVICE_TOKEN`, `MCP_CLIENT_TOKENS` | `LOYALTY_API_TIMEOUT_SECONDS`, `LOYALTY_DEFAULT_PROGRAM`, `MCP_ALLOWED_HOSTS`, `MCP_ALLOWED_ORIGINS` |
| GitHub Actions | secret `RESEND_API_KEY`; variables `CI_REPORT_FROM`, `CI_REPORT_TO` | |

## 9. Runbook: known failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| API returns `503 Database is temporarily unavailable` | The Supabase pooler is full or the project is paused | Check the Supabase status and project. Make sure `DATABASE_URL` uses port 6543. |
| `EMAXCONNSESSION max clients reached` in the logs | `DATABASE_URL` points at the session pooler on port 5432 | Switch to the transaction pooler URL. The API rewrites it and logs a warning, but the setting should still be fixed. |
| `/doi/trigger` or `/auth/*` return `500` quoting `Resend 403 ... domain is not verified` | `EMAIL_FROM` is not on a verified domain | Verify the domain in Resend. |
| `/doi/trigger` returns `502` | Resend is rate-limiting or down, or the network failed | Retry. Check the Resend status page. |
| Logo upload returns `503` | `SUPABASE_URL` or `SUPABASE_SERVICE_ROLE_KEY` is not set | Set both on the API project. |
| `type: "link"` DOI returns `500` | `CLIENT_BASE_URL` is not set | Set it to the public URL of the client. |
| MCP returns `421` | The host is not in the allowed list | Add the host to `MCP_ALLOWED_HOSTS`. |
| Admin console says "Cannot reach the API" | `API_BASE_URL` is wrong, or the API is down | Check `API_BASE_URL` and the API's `/health`. |
| Data saved to the wrong program | A caller left out `X-Program-Id` | Search the logs for "fell back to the default program". |
| `🔴 FAILED` CI email | A regression, or Postgres was unavailable on the runner | Open the run link in the email. The failing log tail is included. |

## 10. Known gaps and recommendations

| # | Gap | Recommendation |
|---|---|---|
| 1 | The regression scripts don't run in CI | Add a step to `api-tests.yml` that runs every `tests/regression/test_*.py`. |
| 2 | The client and the MCP server have no error monitoring | Add `@sentry/nextjs` to the client, and `sentry_sdk` to the MCP server with the same scrubbing rules. |
| 3 | `/health` does not check the database | Add a deep health check (`SELECT 1`) for uptime monitors, and keep `/health` cheap. |
| 4 | No uptime alerting is set up in the repo | Point an uptime monitor at `/health` and `/healthz`, or use Sentry Crons or Uptime. |
| 5 | `SENTRY_TRACES_SAMPLE_RATE` defaults to `1.0` | Lower it in production once traffic grows. |
| 6 | The admin login lockout is held in memory per instance | On serverless, each instance has its own lockout. Move it to a shared store if brute force becomes a concern. |
| 7 | One shared `API_TOKEN` for every backend caller | Consider a separate token for each caller (client, MCP, each external system), so one can be revoked without affecting the others. |
| 8 | The client has no tests | Start with Playwright smoke tests for sign-in and the main admin flows. |
| 9 | No Python lint or type check runs in CI | Add `ruff`, and optionally `mypy`, to the API and MCP workflows. |
