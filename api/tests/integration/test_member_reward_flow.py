"""End to end flow over the member and reward routes.

One member and one reward are carried through every step, in order, the way a
real client would use them: create the member, read and edit it, move points
around, then create a reward, hand it over both ways, and clean both up.

The tests share state deliberately, so they run top to bottom in this file. A
step whose input never arrived is skipped rather than failed, which keeps the
first real failure the only thing you have to read.

The member is deleted before the reward, and that order is required rather than
a preference. `redemptions.reward_id` is NOT NULL with no cascade, so deleting a
reward that anyone has redeemed answers 409. Deleting the member first removes
their redemptions, which leaves the reward free to go.
"""

import uuid

import pytest

MEMBER_NAME = "Ada Lovelace"
UPDATED_NAME = "Ada King"
UPDATED_PHONE = "+15550100"

EARN_POINTS = 500
BURN_POINTS = 100
REWARD_COST = 50

BALANCE_AFTER_EARN = EARN_POINTS
BALANCE_AFTER_BURN = BALANCE_AFTER_EARN - BURN_POINTS
BALANCE_AFTER_REDEEM = BALANCE_AFTER_BURN - REWARD_COST


def _need(state: dict, key: str):
    if key not in state:
        pytest.skip(f"no {key} from an earlier step")
    return state[key]


def test_create_member(api, state):
    # example.com, not .test: the email validator rejects reserved TLDs.
    email = f"ada-{uuid.uuid4().hex[:12]}@example.com"
    response = api.post("/members", json={"name": MEMBER_NAME, "email": email})

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == MEMBER_NAME
    assert body["email"] == email
    # The house rule: responses are camelCase.
    assert body["pointsBalance"] == 0
    assert body["isEmailVerified"] is False

    state["member_id"] = body["id"]
    state["email"] = email


def test_get_member(api, state):
    member_id = _need(state, "member_id")
    response = api.get(f"/members/{member_id}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == member_id
    assert body["name"] == MEMBER_NAME
    assert body["email"] == state["email"]
    assert body["segments"] == []


def test_update_member(api, state):
    member_id = _need(state, "member_id")
    response = api.patch(
        f"/members/{member_id}", json={"name": UPDATED_NAME, "phone": UPDATED_PHONE}
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["name"] == UPDATED_NAME
    assert body["phone"] == UPDATED_PHONE
    # Fields left out of the patch keep their value.
    assert body["email"] == state["email"]


def test_get_balance(api, state):
    member_id = _need(state, "member_id")
    response = api.get(f"/members/{member_id}/balance")

    assert response.status_code == 200, response.text
    assert response.json()["pointsBalance"] == 0


def test_earn_points(api, state):
    member_id = _need(state, "member_id")
    response = api.post(
        f"/members/{member_id}/points/earn",
        json={"points": EARN_POINTS, "description": "Flow test earn"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["type"] == "earn"
    # No tiers exist in a fresh database, so no multiplier is applied.
    assert body["points"] == EARN_POINTS

    balance = api.get(f"/members/{member_id}/balance")
    assert balance.json()["pointsBalance"] == BALANCE_AFTER_EARN


def test_burn_points(api, state):
    member_id = _need(state, "member_id")
    response = api.post(
        f"/members/{member_id}/points/burn",
        json={"points": BURN_POINTS, "description": "Flow test burn"},
    )

    assert response.status_code == 201, response.text
    assert response.json()["type"] == "spend"

    balance = api.get(f"/members/{member_id}/balance")
    assert balance.json()["pointsBalance"] == BALANCE_AFTER_BURN


def test_create_reward(api, state):
    response = api.post(
        "/rewards",
        json={
            "name": f"Flow test reward {uuid.uuid4().hex[:8]}",
            "description": "Created by the API flow test",
            "pointsCost": REWARD_COST,
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["pointsCost"] == REWARD_COST
    assert body["isActive"] is True

    state["reward_id"] = body["id"]


def test_assign_prize(api, state):
    member_id = _need(state, "member_id")
    reward_id = _need(state, "reward_id")
    response = api.post(f"/members/{member_id}/prizes/{reward_id}")

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["source"] == "assigned"
    # A prize is a gift, so nothing is debited.
    assert body["pointsSpent"] == 0

    balance = api.get(f"/members/{member_id}/balance")
    assert balance.json()["pointsBalance"] == BALANCE_AFTER_BURN


def test_redeem_reward(api, state):
    member_id = _need(state, "member_id")
    reward_id = _need(state, "reward_id")
    response = api.post(f"/members/{member_id}/redeem/{reward_id}")

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["source"] == "redeemed"
    assert body["pointsSpent"] == REWARD_COST

    balance = api.get(f"/members/{member_id}/balance")
    assert balance.json()["pointsBalance"] == BALANCE_AFTER_REDEEM


def test_delete_member(api, state):
    member_id = _need(state, "member_id")
    response = api.delete(f"/members/{member_id}")

    assert response.status_code == 204, response.text
    assert api.get(f"/members/{member_id}").status_code == 404


def test_delete_reward(api, state):
    reward_id = _need(state, "reward_id")
    response = api.delete(f"/rewards/{reward_id}")

    assert response.status_code == 204, response.text
    assert api.get(f"/rewards/{reward_id}").status_code == 404
