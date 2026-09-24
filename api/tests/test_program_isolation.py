"""Regression test for program isolation.

Programs exist so two demo datasets can share one database without ever
seeing each other. That guarantee is only worth anything if it holds on
every path, so this covers reads, writes, fetch-by-id, name collisions,
balances, tier multipliers, header resolution and deletion.

The one thing deliberately shared is member identity: the same email is one
person across programs, while their points, tier and progress are separate.

Runs against an in-memory SQLite database. It never touches Supabase and
never sends mail.

Run: ./venv/bin/python -m tests.test_program_isolation
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql://u:p@h:6543/postgres")
os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("RESEND_API_KEY", "test-resend-key")
os.environ.setdefault("DOI_FROM_EMAIL", "noreply@example.com")

import sqlalchemy
from fastapi.testclient import TestClient
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

import app.core.database as database

# One shared in-memory connection: SQLite drops the database when the last
# connection closes, and the app's NullPool closes one after every request.
database.engine = sqlalchemy.create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
database.SessionLocal.configure(bind=database.engine)


@compiles(JSONB, "sqlite")
def _jsonb_on_sqlite(type_, compiler, **kw):  # postgres-only type
    return "JSON"


from app.main import app  # noqa: E402 - must be imported after the engine swap
from app.models import Member, MemberAttribute  # noqa: E402

# ...as must these, postgres-only defaults SQLite cannot render.
Member.__table__.c.custom_attributes.server_default = None
MemberAttribute.__table__.c.options.server_default = None
database.Base.metadata.create_all(bind=database.engine)

AUTH = {"Authorization": "Bearer test-token"}
client = TestClient(app, raise_server_exceptions=False)

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def headers(program: str | None = None) -> dict:
    return AUTH if program is None else {**AUTH, "X-Program-Id": program}


def post(path: str, body: dict, program: str | None = None):
    return client.post(path, json=body, headers=headers(program))


def get(path: str, program: str | None = None):
    return client.get(path, headers=headers(program))


def make_program(name: str, slug: str, is_default: bool = False) -> str:
    response = post("/programs", {"name": name, "slug": slug, "isDefault": is_default})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def main() -> None:
    retail = make_program("Retail Demo", "retail-demo", is_default=True)
    airline = make_program("Airline Demo", "airline-demo")

    # 1 & 2. A reward created in one program is invisible in the other.
    created = post("/rewards", {"name": "Free Coffee", "pointsCost": 100}, "retail-demo")
    check(created.status_code == 201, f"creating a reward answered {created.status_code}")
    reward_id = created.json()["id"]

    retail_rewards = get("/rewards", "retail-demo").json()
    airline_rewards = get("/rewards", "airline-demo").json()
    check(len(retail_rewards) == 1, f"retail sees {len(retail_rewards)} rewards, expected 1")
    check(airline_rewards == [], f"airline sees {airline_rewards}, expected no rewards")

    # 3. Reaching another program's row by id is a 404, not a 403: the caller
    # has no business learning it exists.
    foreign = get(f"/rewards/{reward_id}", "airline-demo")
    check(foreign.status_code == 404, f"cross-program fetch answered {foreign.status_code}, expected 404")

    # 4. The same name in two programs, which the old global unique constraints
    # made impossible.
    def at_least(points: int) -> list[dict]:
        return [{"field": "member.pointsBalance", "operator": "gte", "value": points}]

    gold_retail = post(
        "/tiers", {"name": "Gold", "conditions": at_least(0), "multiplier": 2.0}, "retail-demo"
    )
    gold_airline = post("/tiers", {"name": "Gold", "conditions": at_least(5000)}, "airline-demo")
    check(gold_retail.status_code == 201, f"first Gold tier answered {gold_retail.status_code}")
    check(
        gold_airline.status_code == 201,
        f"second Gold tier answered {gold_airline.status_code}: {gold_airline.text}",
    )
    duplicate = post("/tiers", {"name": "Gold", "conditions": at_least(10)}, "retail-demo")
    check(duplicate.status_code == 400, f"duplicate tier within one program answered {duplicate.status_code}")

    # 5. One person, a membership in every program, separate balances.
    # Members are global: creating someone in one program enrols them in all of
    # them at once, so there is no second "join" call to make.
    email = "shared@example.com"
    in_retail = post("/members", {"name": "Shared Person", "email": email}, "retail-demo")
    check(in_retail.status_code == 201, f"creating a member answered {in_retail.status_code}")
    retail_member = in_retail.json()["id"]
    # A member id means nothing without the program it is addressable from, so
    # every membership says which one it belongs to.
    check(
        in_retail.json().get("programId") == retail,
        f"a membership did not carry its program: {in_retail.json().get('programId')}",
    )

    # The same email is one person, who already belongs everywhere - so this is
    # a duplicate rather than an enrolment, in either program.
    for slug in ("retail-demo", "airline-demo"):
        again = post("/members", {"name": "Shared Person", "email": email}, slug)
        check(
            again.status_code == 400,
            f"re-creating an existing person in {slug} answered {again.status_code}",
        )

    # Their airline membership exists regardless, with its own id.
    memberships = get(f"/members/{retail_member}/programs", "retail-demo").json()
    by_id = {p["id"]: p["memberId"] for p in memberships}
    check(
        all(by_id.get(p) for p in (retail, airline)),
        f"expected a membership in every program, got {by_id}",
    )
    airline_member = by_id[airline]
    check(retail_member != airline_member, "the two memberships share an id")

    # 6. Retail's Gold tier doubles points at zero balance; airline has no tier
    # the member qualifies for, so its multiplier must not leak across.
    post(f"/members/{retail_member}/points/earn", {"points": 50}, "retail-demo")
    post(f"/members/{airline_member}/points/earn", {"points": 50}, "airline-demo")

    retail_balance = get(f"/members/{retail_member}/balance", "retail-demo").json()["pointsBalance"]
    airline_balance = get(f"/members/{airline_member}/balance", "airline-demo").json()["pointsBalance"]
    check(retail_balance == 100, f"retail balance is {retail_balance}, expected 100 (2x tier)")
    check(airline_balance == 50, f"airline balance is {airline_balance}, expected 50 (no tier)")

    # The membership is addressable only from its own program.
    crossed = get(f"/members/{retail_member}/balance", "airline-demo")
    check(crossed.status_code == 404, f"cross-program balance answered {crossed.status_code}, expected 404")

    # 6b. A member can see where else they are a member, which is what the
    # member app's program switcher is built on.
    listed = get(f"/members/{retail_member}/programs", "retail-demo")
    check(listed.status_code == 200, f"listing a member's programs answered {listed.status_code}")
    by_slug = {p["slug"]: p for p in listed.json()}
    check(
        by_slug["retail-demo"]["memberId"] == retail_member
        and by_slug["airline-demo"]["memberId"] == airline_member,
        f"a member's programs did not carry their two membership ids: {listed.json()}",
    )

    # Switching to a program they already belong to returns that same
    # membership rather than creating a second one.
    switched = post(f"/members/{retail_member}/programs/{airline}", {}, "retail-demo")
    check(switched.status_code == 200, f"switching program answered {switched.status_code}: {switched.text}")
    check(
        switched.json()["id"] == airline_member,
        "switching to a joined program created a duplicate membership",
    )
    check(
        switched.json()["pointsBalance"] == 50,
        "switching lost the balance the member already had there",
    )

    # Someone created in one program already holds a membership in the other,
    # sitting at zero while their retail balance is untouched.
    newcomer = post("/members", {"name": "Retail Only", "email": "solo@example.com"}, "retail-demo")
    solo = newcomer.json()["id"]
    post(f"/members/{solo}/points/earn", {"points": 30}, "retail-demo")
    elsewhere = {
        p["slug"]: p for p in get(f"/members/{solo}/programs", "retail-demo").json()
    }
    check(
        elsewhere["airline-demo"]["memberId"] is not None,
        "a new person was not enrolled in every program",
    )
    switched = post(f"/members/{solo}/programs/{airline}", {}, "retail-demo")
    check(switched.status_code == 200, f"switching program answered {switched.status_code}: {switched.text}")
    check(
        switched.json()["id"] == elsewhere["airline-demo"]["memberId"],
        "switching created a second membership instead of returning the existing one",
    )
    check(
        switched.json()["id"] != solo and switched.json()["pointsBalance"] == 0,
        f"the other program's membership did not start from zero: {switched.json()}",
    )
    check(
        switched.json()["email"] == "solo@example.com",
        "the membership lost the person behind it",
    )

    # 7. No header resolves to the default program.
    default_rewards = get("/rewards").json()
    check(
        len(default_rewards) == 1 and default_rewards[0]["name"] == "Free Coffee",
        f"a request without a program header saw {default_rewards}, expected retail's reward",
    )

    # 8. An unknown program names what it could not find.
    unknown = get("/rewards", "no-such-program")
    check(unknown.status_code == 404, f"unknown program answered {unknown.status_code}, expected 404")
    check("no-such-program" in unknown.text, "the 404 does not name the program that was not found")

    # A slug and the program's uuid address the same dataset.
    by_uuid = get("/rewards", airline)
    check(by_uuid.status_code == 200 and by_uuid.json() == [], "addressing a program by uuid did not match its slug")

    # 8b. Members are global in both directions: a program created after people
    # already exist opens holding every one of them, at zero.
    grocery = make_program("Grocery Demo", "grocery-demo")
    roster = get("/members", "grocery-demo").json()
    everyone = get("/members", "retail-demo").json()
    check(
        len(roster) == len(everyone),
        f"new program holds {len(roster)} members, expected all {len(everyone)}",
    )
    check(
        all(m["pointsBalance"] == 0 for m in roster),
        "a new program's memberships did not all start at zero",
    )
    # Enrolling everyone must not have disturbed their standing elsewhere.
    retail_after = get(f"/members/{retail_member}/balance", "retail-demo").json()["pointsBalance"]
    check(
        retail_after == retail_balance,
        f"retail balance changed to {retail_after} when a program was added",
    )
    client.delete(f"/programs/{grocery}", headers=AUTH)

    # 9. Deleting a program takes its own rows and nothing else.
    post("/rewards", {"name": "Lounge Pass", "pointsCost": 500}, "airline-demo")
    deleted = client.delete(f"/programs/{airline}", headers=AUTH)
    check(deleted.status_code == 204, f"deleting a program answered {deleted.status_code}: {deleted.text}")

    survivors = get("/rewards", "retail-demo").json()
    check(len(survivors) == 1, f"retail lost rows when airline was deleted: {survivors}")
    still_there = get(f"/members/{retail_member}/balance", "retail-demo")
    check(still_there.status_code == 200, "retail's member did not survive deleting the other program")

    # The default program is what a header-less request falls back to, so it
    # cannot be deleted out from under those callers.
    protected = client.delete(f"/programs/{retail}", headers=AUTH)
    check(protected.status_code == 400, f"deleting the default program answered {protected.status_code}")

    # 10. Nor can it be un-defaulted, which is the same hole by another route:
    # an edit that merely renames it must not silently leave zero defaults.
    renamed = client.patch(
        f"/programs/{retail}",
        json={"name": "Retail Demo Renamed", "isDefault": False},
        headers=AUTH,
    )
    check(renamed.status_code == 400, f"unsetting the default answered {renamed.status_code}")
    still_default = get(f"/programs/{retail}").json()
    check(still_default["isDefault"], "the default flag was cleared by a rejected edit")
    check(
        still_default["name"] == "Retail Demo",
        f"a rejected edit renamed the program anyway: {still_default['name']!r}",
    )

    if failures:
        print("FAIL:")
        for failure in failures:
            print("  -", failure)
        raise SystemExit(1)
    print("OK: programs isolate rewards, tiers, members, balances and deletion")


if __name__ == "__main__":
    main()
