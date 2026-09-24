"""Regression test for tier eligibility: points, purchase spend, segments and
custom attributes, combined with AND, and re-checked whenever any of them (or
a tier's own definition) changes.

Runs against an in-memory SQLite database. It never touches Supabase and
never sends mail.

Run: ./venv/bin/python -m tests.test_tier_conditions
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
PROGRAM = "tiers-demo"

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def call(method: str, path: str, body: dict | None = None):
    return client.request(method, path, json=body, headers={**AUTH, "X-Program-Id": PROGRAM})


def created(response, what: str) -> dict:
    assert response.status_code == 201, f"creating {what} answered {response.status_code}: {response.text}"
    return response.json()


def ok(response, what: str, status: int = 200) -> dict | None:
    assert response.status_code == status, (
        f"{what} answered {response.status_code}, expected {status}: {response.text}"
    )
    return response.json() if response.content else None


def tier_name(member_id: str) -> str | None:
    member = ok(call("GET", f"/members/{member_id}"), "fetching the member")
    return member["tier"]["name"] if member["tier"] else None


def main() -> None:
    created(client.post("/programs", json={"name": "Tiers", "slug": PROGRAM}, headers=AUTH), "a program")

    created(call("POST", "/tiers", {"name": "Base", "rank": 0, "conditions": []}), "the Base tier")
    vip = created(
        call(
            "POST",
            "/tiers",
            {
                "name": "VIP",
                "rank": 10,
                "multiplier": 2.0,
                # AND, not OR: neither condition alone is enough.
                "conditions": [
                    {"field": "member.pointsBalance", "operator": "gte", "value": 50},
                    {"field": "member.purchaseSpendCents", "operator": "gte", "value": 1000},
                ],
            },
        ),
        "the VIP tier",
    )
    segment = created(call("POST", "/segments", {"name": "Newsletter"}), "a segment")
    loyal = created(
        call(
            "POST",
            "/tiers",
            {
                "name": "Loyal Subscriber",
                "rank": 5,
                "conditions": [{"field": "member.segments", "operator": "contains", "value": segment["id"]}],
            },
        ),
        "the Loyal Subscriber tier",
    )
    product = created(
        call("POST", "/products", {"name": "Widget", "priceCents": 1500}), "a product"
    )

    member = created(call("POST", "/members", {"name": "Ada", "email": "ada@example.com"}), "a member")

    # 1. Nothing earned or spent yet: only the catch-all Base tier's empty
    # conditions match.
    check(tier_name(member["id"]) == "Base", f"a fresh member is in {tier_name(member['id'])!r}, expected Base")

    # 2. Enough points but no spend: VIP's points condition alone isn't
    # enough, since both of its conditions must hold.
    ok(call("POST", f"/members/{member['id']}/points/earn", {"points": 100}), "earning points", status=201)
    check(
        tier_name(member["id"]) == "Base",
        f"100 points alone put the member in {tier_name(member['id'])!r}, expected Base (VIP needs spend too)",
    )

    # 3. Spend enough too: now both of VIP's conditions hold, and a purchase
    # (not a points transaction) is what tips it over - proving purchase
    # spend is itself read live, not just points.
    ok(
        call("POST", f"/members/{member['id']}/purchases", {"productId": product["id"], "quantity": 1}),
        "a purchase",
        status=201,
    )
    check(tier_name(member["id"]) == "VIP", f"member with 100pts/1500cents spend is in {tier_name(member['id'])!r}, expected VIP")

    # The multiplier actually applied: 100 earned once at 1x, then another 100
    # should earn 200 at VIP's 2x.
    balance = ok(call("GET", f"/members/{member['id']}/balance"), "balance")["pointsBalance"]
    ok(call("POST", f"/members/{member['id']}/points/earn", {"points": 100}), "earning more points", status=201)
    new_balance = ok(call("GET", f"/members/{member['id']}/balance"), "balance")["pointsBalance"]
    check(
        new_balance - balance == 200,
        f"earning 100 points at VIP gained {new_balance - balance}, expected 200 (2x multiplier)",
    )

    # 4. A segment-only condition, changed with no points or purchase
    # involved at all - proves segment membership alone re-triggers apply_tier.
    other = created(call("POST", "/members", {"name": "Bob", "email": "bob@example.com"}), "a member")
    check(tier_name(other["id"]) == "Base", "a fresh second member should start in Base")
    ok(
        call("POST", f"/segments/{segment['id']}/assign", {"memberIds": [other["id"]]}),
        "assigning the segment",
    )
    check(
        tier_name(other["id"]) == "Loyal Subscriber",
        f"member added to the segment is in {tier_name(other['id'])!r}, expected Loyal Subscriber",
    )

    # 5. Editing a tier's own conditions re-checks members who changed
    # nothing themselves: drop VIP's spend requirement, and Bob (50+ points,
    # no purchases) should immediately qualify.
    ok(call("POST", f"/members/{other['id']}/points/earn", {"points": 50}), "earning points for Bob", status=201)
    check(tier_name(other["id"]) == "Loyal Subscriber", "Bob should still be Loyal Subscriber before the edit")
    ok(
        call(
            "PATCH",
            f"/tiers/{vip['id']}",
            {"conditions": [{"field": "member.pointsBalance", "operator": "gte", "value": 50}]},
        ),
        "loosening VIP's conditions",
    )
    check(
        tier_name(other["id"]) == "VIP",
        f"after loosening VIP, Bob is in {tier_name(other['id'])!r}, expected VIP (outranks Loyal Subscriber)",
    )

    # 6. Deleting the tier a member holds re-checks them rather than just
    # nulling the column: Bob falls back to Loyal Subscriber, not tierless.
    ok(call("DELETE", f"/tiers/{vip['id']}"), "deleting VIP", status=204)
    check(
        tier_name(other["id"]) == "Loyal Subscriber",
        f"after deleting VIP, Bob is in {tier_name(other['id'])!r}, expected Loyal Subscriber",
    )

    # 7. A condition combining a custom attribute with points, both ANDed -
    # the "any other param" part of the ask.
    attr = created(
        call("POST", "/member-attributes", {"label": "VIP tag", "type": "boolean"}), "an attribute"
    )
    created(
        call(
            "POST",
            "/tiers",
            {
                "name": "Tagged Elite",
                "rank": 20,
                "conditions": [
                    {"field": "member.pointsBalance", "operator": "gte", "value": 10},
                    {"field": f"member.customAttributes.{attr['key']}", "operator": "eq", "value": True},
                ],
            },
        ),
        "the Tagged Elite tier",
    )
    check(
        tier_name(other["id"]) != "Tagged Elite",
        "Bob shouldn't qualify for Tagged Elite before the custom attribute is set",
    )
    ok(
        call("PATCH", f"/members/{other['id']}", {"customAttributes": {attr["key"]: True}}),
        "setting the custom attribute",
    )
    check(
        tier_name(other["id"]) == "Tagged Elite",
        f"after setting the tag, Bob is in {tier_name(other['id'])!r}, expected Tagged Elite",
    )

    if failures:
        print(f"FAILED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        raise SystemExit(1)
    print("OK: tiers combine points, purchase spend, segments and custom attributes, and stay in sync")


if __name__ == "__main__":
    main()
