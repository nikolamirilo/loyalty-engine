"""End to end flow over events and their rules, against a real Postgres.

Defines an event type with two rules, then sends events for one member and
checks what the rules did: points per euro, a once-per-member welcome that
grants a reward and copies an event attribute onto the member, and a retry
with the same eventId that runs nothing. Deleting the event type at the end
must leave the member's history in place.

``tests/test_event_rules.py`` covers every effect and validation on SQLite;
this file exists for what only Postgres exercises: JSONB columns, the unique
eventId constraint, and the cascades.
"""

import uuid

import pytest

AMOUNT_FIRST = 30
AMOUNT_SECOND = 10


def _need(state: dict, key: str):
    if key not in state:
        pytest.skip(f"no {key} from an earlier step")
    return state[key]


def test_define_event_type(api, state):
    response = api.post(
        "/event-types",
        json={
            "name": "Order placed",
            "attributes": [
                {"label": "Amount", "type": "number"},
                {"label": "Store", "type": "text"},
            ],
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["key"] == "orderPlaced"
    assert [a["key"] for a in body["attributes"]] == ["amount", "store"]
    assert body["rules"] == []
    state["event_type_id"] = body["id"]


def test_create_rules(api, state):
    event_type_id = _need(state, "event_type_id")

    attribute = api.post("/member-attributes", json={"label": "Favourite store", "type": "text"})
    assert attribute.status_code == 201, attribute.text
    reward = api.post("/rewards", json={"name": f"Welcome gift {uuid.uuid4().hex[:6]}", "pointsCost": 100})
    assert reward.status_code == 201, reward.text
    state["reward_id"] = reward.json()["id"]

    per_euro = api.post(
        f"/event-types/{event_type_id}/rules",
        json={
            "name": "1 point per euro",
            "effects": [{"type": "addPoints", "fromAttribute": "amount"}],
        },
    )
    assert per_euro.status_code == 201, per_euro.text

    welcome = api.post(
        f"/event-types/{event_type_id}/rules",
        json={
            "name": "Welcome",
            "limitPerMember": 1,
            "effects": [
                {"type": "grantReward", "rewardId": state["reward_id"]},
                {
                    "type": "updateMember",
                    "fields": [{"field": "member.customAttributes.favouriteStore", "fromAttribute": "store"}],
                },
            ],
        },
    )
    assert welcome.status_code == 201, welcome.text
    assert welcome.json()["limitPerMember"] == 1


def test_create_member(api, state):
    email = f"eve-{uuid.uuid4().hex[:12]}@example.com"
    response = api.post("/members", json={"name": "Eve", "email": email})
    assert response.status_code == 201, response.text
    state["event_member_id"] = response.json()["id"]


def test_send_event(api, state):
    member_id = _need(state, "event_member_id")
    response = api.post(
        "/events",
        json={
            "memberId": member_id,
            "type": "orderPlaced",
            "attributes": {"amount": AMOUNT_FIRST, "store": "Berlin"},
            "eventId": "order-1",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert [e["type"] for e in body["effects"]] == ["addPoints", "grantReward", "updateMember"]
    assert body["effects"][0]["points"] == AMOUNT_FIRST
    assert not any(e["skipped"] for e in body["effects"])
    state["first_event_id"] = body["id"]

    member = api.get(f"/members/{member_id}").json()
    assert member["pointsBalance"] == AMOUNT_FIRST
    assert member["customAttributes"]["favouriteStore"] == "Berlin"
    assert len(api.get(f"/members/{member_id}/prizes").json()) == 1


def test_retry_runs_nothing(api, state):
    member_id = _need(state, "event_member_id")
    response = api.post(
        "/events",
        json={"memberId": member_id, "type": "orderPlaced", "attributes": {"amount": 999}, "eventId": "order-1"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["id"] == state["first_event_id"]
    assert api.get(f"/members/{member_id}/balance").json()["pointsBalance"] == AMOUNT_FIRST


def test_limit_per_member(api, state):
    member_id = _need(state, "event_member_id")
    response = api.post(
        "/events",
        json={"memberId": member_id, "type": "orderPlaced", "attributes": {"amount": AMOUNT_SECOND, "store": "Munich"}},
    )

    assert response.status_code == 201, response.text
    # Only the per-euro rule: the welcome rule already ran its one time.
    assert [e["type"] for e in response.json()["effects"]] == ["addPoints"]
    member = api.get(f"/members/{member_id}").json()
    assert member["pointsBalance"] == AMOUNT_FIRST + AMOUNT_SECOND
    assert member["customAttributes"]["favouriteStore"] == "Berlin"


def test_list_member_events(api, state):
    member_id = _need(state, "event_member_id")
    response = api.get(f"/members/{member_id}/events")

    assert response.status_code == 200, response.text
    events = response.json()
    assert len(events) == 2
    assert events[1]["id"] == state["first_event_id"]  # newest first
    assert events[1]["eventId"] == "order-1"


def test_delete_event_type_keeps_history(api, state):
    event_type_id = _need(state, "event_type_id")
    member_id = _need(state, "event_member_id")

    assert api.delete(f"/event-types/{event_type_id}").status_code == 204
    events = api.get(f"/members/{member_id}/events").json()
    assert len(events) == 2
    assert events[0]["name"] == "orderPlaced"  # the type's key, once the type is gone


def test_delete_event_member(api, state):
    member_id = _need(state, "event_member_id")
    assert api.delete(f"/members/{member_id}").status_code == 204
    # The member's prize is gone with them, which frees the reward to be deleted.
    reward_id = _need(state, "reward_id")
    assert api.delete(f"/rewards/{reward_id}").status_code == 204
