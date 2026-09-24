"""Regression test for member events and the rule engine.

Defines an event type, attaches rules covering every effect, then sends
events for one member and checks what each rule did: points (with the tier
multiplier), segments, prizes, challenge progress, member field updates,
the once-per-member limit and eventId retries. Also covers the checks a
rule must pass when saved, and that events stay inside their program.

Runs against an in-memory SQLite database. It never touches Supabase and
never sends mail.

Run: ./venv/bin/python -m tests.test_event_rules
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
PROGRAM = "events-demo"

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def call(method: str, path: str, body: dict | None = None, program: str = PROGRAM):
    return client.request(method, path, json=body, headers={**AUTH, "X-Program-Id": program})


def created(response, what: str) -> dict:
    assert response.status_code == 201, f"creating {what} answered {response.status_code}: {response.text}"
    return response.json()


def balance(member_id: str) -> int:
    return call("GET", f"/members/{member_id}/balance").json()["pointsBalance"]


def summaries(event: dict) -> list[str]:
    return [e["summary"] for e in event["effects"]]


def send(member_id: str, attributes: dict, event_id: str | None = None, type_: str = "orderPlaced"):
    body = {"memberId": member_id, "type": type_, "attributes": attributes}
    if event_id:
        body["eventId"] = event_id
    return call("POST", "/events", body)


def main() -> None:
    created(client.post("/programs", json={"name": "Events", "slug": PROGRAM}, headers=AUTH), "a program")
    created(client.post("/programs", json={"name": "Other", "slug": "other"}, headers=AUTH), "a program")

    created(call("POST", "/tiers", {"name": "Base", "minPoints": 0, "multiplier": 1.0}), "a tier")
    created(call("POST", "/tiers", {"name": "Gold", "minPoints": 500, "multiplier": 2.0}), "a tier")
    vip = created(call("POST", "/segments", {"name": "VIP"}), "a segment")["id"]
    big = created(call("POST", "/segments", {"name": "Big spenders"}), "a segment")["id"]
    coffee = created(call("POST", "/rewards", {"name": "Free coffee", "pointsCost": 100, "stock": 1}), "a reward")["id"]
    orders = created(call("POST", "/challenges", {"name": "3 orders", "targetValue": 3}), "a challenge")["id"]
    created(
        call("POST", "/member-attributes", {"label": "Favourite store", "type": "select", "options": ["Berlin", "Munich"]}),
        "an attribute",
    )
    created(call("POST", "/member-attributes", {"label": "Newsletter opt in", "type": "boolean"}), "an attribute")
    member = created(call("POST", "/members", {"name": "Ada", "email": "ada@example.com"}), "a member")["id"]
    created(call("POST", f"/members/{member}/challenges/{orders}"), "a challenge assignment")

    # ── defining the event ──────────────────────────────────────────────────
    order = created(
        call(
            "POST",
            "/event-types",
            {
                "name": "Order placed",
                "description": "Sent by the shop",
                "attributes": [
                    {"label": "Amount", "type": "number"},
                    {"label": "Channel", "type": "select", "options": ["Online", "App"]},
                    {"label": "Store", "type": "select", "options": ["Berlin", "Munich"]},
                    {"label": "Phone", "type": "text"},
                ],
            },
        ),
        "an event type",
    )
    order_id = order["id"]
    check(order["key"] == "orderPlaced", f"event key was {order['key']!r}")
    check(
        [a["key"] for a in order["attributes"]] == ["amount", "channel", "store", "phone"],
        f"attribute keys were {[a['key'] for a in order['attributes']]}",
    )
    again = call("POST", "/event-types", {"name": "Order placed!"})
    check(again.status_code == 400, f"a duplicate event key answered {again.status_code}")

    rules = f"/event-types/{order_id}/rules"

    # ── rules that must be refused when saved ───────────────────────────────
    def refused(body: dict, why: str, status: int = 400) -> None:
        response = call("POST", rules, {"name": "Bad", **body})
        check(response.status_code == status, f"{why}: answered {response.status_code} {response.text}")

    points = {"type": "addPoints", "points": 1}
    refused({"conditions": [{"field": "event.attributes.nope", "operator": "eq", "value": 1}], "effects": [points]}, "unknown field")
    refused({"conditions": [{"field": "event.attributes.channel", "operator": "gt", "value": "App"}], "effects": [points]}, "gt on a dropdown")
    refused({"conditions": [{"field": "event.attributes.channel", "operator": "eq", "value": "Fax"}], "effects": [points]}, "value outside the options")
    refused({"effects": [{"type": "addPoints", "fromAttribute": "channel"}]}, "points from a non-number attribute")
    refused({"effects": [{"type": "addPoints", "points": 1, "fromAttribute": "amount"}]}, "points both fixed and from an attribute")
    refused({"effects": [{"type": "addPoints"}]}, "points with no amount")
    refused(
        {"effects": [{"type": "addChallengeProgress", "challengeId": orders, "fromAttribute": "store"}]},
        "progress from a non-number attribute",
    )
    refused({"effects": [{"type": "burnPoints", "fromAttribute": "channel"}]}, "burning from a non-number attribute")
    refused({"effects": [{"type": "grantReward", "rewardId": "00000000-0000-0000-0000-000000000000"}]}, "unknown reward", 404)
    refused({"effects": [{"type": "assignChallenge", "challengeId": "00000000-0000-0000-0000-000000000000"}]}, "unknown challenge", 404)
    refused({"effects": [{"type": "removeFromSegment", "segmentId": "00000000-0000-0000-0000-000000000000"}]}, "unknown segment", 404)
    refused({"effects": [{"type": "updateMember", "fields": [{"field": "member.email", "value": "x@example.com"}]}]}, "updating email")
    refused(
        {"effects": [{"type": "updateMember", "fields": [{"field": "member.customAttributes.newsletterOptIn", "fromAttribute": "phone"}]}]},
        "copying text into a yes/no field",
    )
    refused({"effects": []}, "a rule with no effects", 422)

    # ── the rules under test ────────────────────────────────────────────────
    per_euro = created(
        call("POST", rules, {"name": "1 point per euro", "effects": [{"type": "addPoints", "fromAttribute": "amount"}]}),
        "a rule",
    )
    created(
        call(
            "POST",
            rules,
            {
                "name": "Big basket",
                "conditions": [{"field": "event.attributes.amount", "operator": "gte", "value": "100"}],
                "effects": [{"type": "addPoints", "points": 50}, {"type": "addToSegment", "segmentId": big}],
            },
        ),
        "a rule",
    )
    gift = created(
        call(
            "POST",
            rules,
            {
                "name": "App VIP gift",
                "conditions": [
                    {"field": "event.attributes.channel", "operator": "eq", "value": "App"},
                    {"field": "member.segments", "operator": "contains", "value": vip},
                ],
                "effects": [{"type": "grantReward", "rewardId": coffee}],
            },
        ),
        "a rule",
    )
    check(gift["conditions"][0]["value"] == "App", f"stored condition was {gift['conditions'][0]}")
    created(
        call(
            "POST",
            rules,
            {
                "name": "Welcome",
                "limitPerMember": 1,
                "effects": [
                    {
                        "type": "updateMember",
                        "fields": [
                            {"field": "member.customAttributes.favouriteStore", "fromAttribute": "store"},
                            {"field": "member.phone", "fromAttribute": "phone"},
                            {"field": "member.customAttributes.newsletterOptIn", "value": "true"},
                        ],
                    }
                ],
            },
        ),
        "a rule",
    )
    created(
        call("POST", rules, {"name": "Order challenge", "effects": [{"type": "addChallengeProgress", "challengeId": orders}]}),
        "a rule",
    )

    # ── event 1: the first order ────────────────────────────────────────────
    first = send(member, {"amount": 40, "channel": "Online", "store": "Berlin", "phone": "+41 1"}, "order-1")
    check(first.status_code == 201, f"first event answered {first.status_code}: {first.text}")
    event = first.json()
    check(
        summaries(event) == [
            "Earned 40 points",
            "Set favourite store to Berlin, phone to +41 1, newsletter opt in to Yes",
            'Added 1 progress to "3 orders"',
        ],
        f"first event did {summaries(event)}",
    )
    check(event["name"] == "Order placed" and event["eventId"] == "order-1", f"first event came back as {event}")
    check(balance(member) == 40, f"balance after the first order was {balance(member)}")
    ada = call("GET", f"/members/{member}").json()
    check(
        ada["customAttributes"] == {"favouriteStore": "Berlin", "newsletterOptIn": True} and ada["phone"] == "+41 1",
        f"member after the first order: {ada['customAttributes']}, phone {ada['phone']}",
    )

    # A retry with the same eventId returns the first result and runs nothing.
    retry = send(member, {"amount": 40}, "order-1")
    check(retry.status_code == 200 and retry.json()["id"] == event["id"], f"a retry answered {retry.status_code}")
    check(balance(member) == 40, f"a retry moved the balance to {balance(member)}")

    # ── event 2: a big basket, and the welcome rule has run its one time ────
    second = send(member, {"amount": 120, "channel": "App", "store": "Munich"}).json()
    check(
        summaries(second) == ["Earned 120 points", "Earned 50 points", 'Added to segment "Big spenders"', 'Added 1 progress to "3 orders"'],
        f"second event did {summaries(second)}",
    )
    check(balance(member) == 210, f"balance after the second order was {balance(member)}")
    ada = call("GET", f"/members/{member}").json()
    check(ada["customAttributes"]["favouriteStore"] == "Berlin", "the once-per-member rule ran twice")
    check(big in [s["id"] for s in ada["segments"]], "the member was not added to Big spenders")

    # ── event 3: now VIP and Gold, so the gift fires and points double ──────
    call("PATCH", f"/members/{member}", {"segmentIds": [vip, big]})
    call("POST", f"/members/{member}/points/earn", {"points": 300})  # 510, Gold
    third = send(member, {"amount": 10, "channel": "App"}).json()
    check(
        summaries(third) == ["Earned 20 points", 'Gave reward "Free coffee"', 'Completed "3 orders"'],
        f"third event did {summaries(third)}",
    )
    check(third["effects"][0]["points"] == 20 and third["effects"][1]["rewardId"] == coffee, f"third event details: {third['effects']}")
    check(balance(member) == 530, f"balance after the third order was {balance(member)}")

    # ── event 4: the reward is out of stock and the challenge is done ───────
    fourth = send(member, {"amount": 10, "channel": "App"}).json()
    skipped = [e["summary"] for e in fourth["effects"] if e["skipped"]]
    check(
        skipped == ['"Free coffee" is inactive or out of stock', '"3 orders": challenge is already completed'],
        f"fourth event skipped {skipped}",
    )
    check(balance(member) == 550, f"balance after the fourth order was {balance(member)}")

    # ── bad events ──────────────────────────────────────────────────────────
    check(send(member, {}, type_="nope").status_code == 400, "an unknown event type was accepted")
    check(send(member, {"colour": "red"}).status_code == 400, "an unknown attribute was accepted")
    check(send(member, {"amount": "lots"}).status_code == 400, "a non-number amount was accepted")
    created(call("POST", "/event-types", {"name": "Paused thing", "isActive": False}), "an event type")
    check(send(member, {}, type_="pausedThing").status_code == 400, "an inactive event type was accepted")
    other_member = created(call("POST", "/members", {"name": "Bo", "email": "bo@example.com"}, "other"), "a member")["id"]
    check(send(other_member, {}).status_code == 404, "a member from another program was accepted")
    check(call("GET", "/event-types", program="other").json() == [], "event types leaked into another program")

    # ── history ─────────────────────────────────────────────────────────────
    history = call("GET", f"/members/{member}/events").json()
    check(len(history) == 4, f"history holds {len(history)} events, expected 4")
    check(history[0]["id"] == fourth["id"], "history is not newest first")
    transactions = call("GET", f"/members/{member}/transactions").json()
    check(
        any(t["description"] == "Order placed: 1 point per euro" for t in transactions),
        "event points left no readable transaction",
    )

    # ── editing the definition and the rules ────────────────────────────────
    keep = [
        {"key": "amount", "label": "Order total", "type": "number"},
        {"key": "channel", "label": "Channel", "type": "select", "options": ["Online", "App"]},
        {"key": "store", "label": "Store", "type": "select", "options": ["Berlin", "Munich"]},
        {"key": "phone", "label": "Phone", "type": "text"},
    ]
    dropped = call("PATCH", f"/event-types/{order_id}", {"attributes": keep[1:]})
    check(dropped.status_code == 400, f"dropping an attribute a rule uses answered {dropped.status_code}")
    retyped = call("PATCH", f"/event-types/{order_id}", {"attributes": [{**keep[0], "type": "text"}, *keep[1:]]})
    check(retyped.status_code == 400, f"changing an attribute's type answered {retyped.status_code}")
    renamed = call("PATCH", f"/event-types/{order_id}", {"attributes": [*keep, {"label": "Coupon", "type": "text"}]})
    check(renamed.status_code == 200, f"renaming and adding attributes answered {renamed.status_code}: {renamed.text}")
    check([a["key"] for a in renamed.json()["attributes"]][-1] == "coupon", "the new attribute got no key")

    paused = call("PATCH", f"{rules}/{per_euro['id']}", {"isActive": False})
    check(paused.status_code == 200 and paused.json()["isActive"] is False, f"pausing a rule answered {paused.status_code}")
    fifth = send(member, {"amount": 5, "channel": "Online"}).json()
    check(not any(e["ruleId"] == per_euro["id"] for e in fifth["effects"]), "a paused rule still ran")

    # ── deleting the definition keeps the history ───────────────────────────
    check(call("DELETE", f"/event-types/{order_id}").status_code == 204, "deleting the event type failed")
    history = call("GET", f"/members/{member}/events").json()
    check(len(history) == 5 and history[0]["name"] == "orderPlaced", f"history after deleting the type: {history[:1]}")

    # ── the progress endpoint still works after moving its logic ────────────
    solo = created(call("POST", "/challenges", {"name": "Solo", "targetValue": 2}), "a challenge")["id"]
    created(call("POST", f"/members/{member}/challenges/{solo}"), "a challenge assignment")
    step = call("POST", f"/members/{member}/challenges/{solo}/progress", {"amount": 1}).json()
    check(step["status"] == "in_progress" and step["currentValue"] == 1, f"manual progress gave {step}")
    done = call("POST", f"/members/{member}/challenges/{solo}/progress", {"amount": 1}).json()
    check(done["status"] == "completed", f"reaching the target gave {done['status']}")
    late = call("POST", f"/members/{member}/challenges/{solo}/progress", {"amount": 1})
    check(late.status_code == 400, f"progress on a completed challenge answered {late.status_code}")

    # ── challenge progress read from an event attribute ─────────────────────
    move = created(call("POST", "/challenges", {"name": "Move 30", "targetValue": 30}), "a challenge")["id"]
    created(call("POST", f"/members/{member}/challenges/{move}"), "a challenge assignment")
    workout = created(
        call("POST", "/event-types", {"name": "Workout", "attributes": [{"label": "Minutes", "type": "number"}]}),
        "an event type",
    )
    stored = created(
        call(
            "POST",
            f"/event-types/{workout['id']}/rules",
            {"name": "Minutes count", "effects": [{"type": "addChallengeProgress", "challengeId": move, "fromAttribute": "minutes"}]},
        ),
        "a rule",
    )["effects"][0]
    check(stored["fromAttribute"] == "minutes" and stored["amount"] is None, f"stored progress effect was {stored}")
    ran = send(member, {"minutes": 20}, type_="workout").json()
    check(summaries(ran) == ['Added 20 progress to "Move 30"'], f"a workout did {summaries(ran)}")
    missing = send(member, {}, type_="workout").json()
    check(summaries(missing) == ["No progress: the event had no minutes"], f"a workout without minutes did {summaries(missing)}")
    finished = send(member, {"minutes": 12}, type_="workout").json()
    check(summaries(finished) == ['Completed "Move 30"'], f"the last workout did {summaries(finished)}")

    # ── burning points, starting a challenge, leaving a segment ─────────────
    redeem = created(
        call("POST", "/event-types", {"name": "Points redeemed", "attributes": [{"label": "Points", "type": "number"}]}),
        "an event type",
    )
    starter = created(call("POST", "/challenges", {"name": "Starter", "targetValue": 5}), "a challenge")["id"]
    created(
        call(
            "POST",
            f"/event-types/{redeem['id']}/rules",
            {
                "name": "Redeemed at the till",
                "effects": [
                    {"type": "burnPoints", "fromAttribute": "points"},
                    {"type": "assignChallenge", "challengeId": starter},
                    {"type": "addChallengeProgress", "challengeId": starter, "amount": 2},
                    {"type": "removeFromSegment", "segmentId": big},
                ],
            },
        ),
        "a rule",
    )
    before = balance(member)
    spent = send(member, {"points": 100}, type_="pointsRedeemed").json()
    check(
        summaries(spent)
        == ["Burned 100 points", 'Assigned challenge "Starter"', 'Added 2 progress to "Starter"', 'Removed from segment "Big spenders"'],
        f"redeeming did {summaries(spent)}",
    )
    check(spent["effects"][0]["points"] == -100, f"a burn reported {spent['effects'][0]['points']} points")
    check(balance(member) == before - 100, f"balance after burning 100 of {before} was {balance(member)}")
    ada = call("GET", f"/members/{member}").json()
    check(big not in [s["id"] for s in ada["segments"]], "the member is still in Big spenders")

    too_many = before * 10
    again = send(member, {"points": too_many}, type_="pointsRedeemed").json()
    check(
        summaries(again)
        == [
            f"Not enough points to burn {too_many}: the member has {before - 100}",
            'Already has the challenge "Starter"',
            'Added 2 progress to "Starter"',
            'Not in "Big spenders"',
        ],
        f"redeeming too much did {summaries(again)}",
    )
    check(balance(member) == before - 100, f"a burn beyond the balance moved it to {balance(member)}")

    if failures:
        print("FAIL:")
        for failure in failures:
            print("  -", failure)
        raise SystemExit(1)
    print("OK: events run their rules, respect limits and retries, and stay in their program")


if __name__ == "__main__":
    main()
