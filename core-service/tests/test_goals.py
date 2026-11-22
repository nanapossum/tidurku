import pytest

from app.events import SleepGoalUpdated, clear_subscribers, subscribe
from app.goals.defaults import DEFAULT_BEDTIME, default_target, healthy_range
from app.goals.models import SleepGoal
from app.identity.models import User


def register_user(client, email="goals@example.com", age=30):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Goal User",
            "email": email,
            "password": "healthy-goal-password",
            "age": age,
        },
    )
    assert response.status_code == 201
    body = response.json()
    return body["user"], {"Authorization": f"Bearer {body['accessToken']}"}


@pytest.mark.parametrize(
    ("age", "expected_range", "expected_target"),
    [
        (13, (9, 11), 10),
        (14, (8, 10), 9),
        (17, (8, 10), 9),
        (18, (7, 9), 8),
        (64, (7, 9), 8),
        (65, (7, 8), 7.5),
    ],
)
def test_healthy_range_and_default_target_boundaries(
    age,
    expected_range,
    expected_target,
):
    assert healthy_range(age) == expected_range
    assert default_target(age) == expected_target


def test_get_goal_returns_default_based_on_age_and_default_bedtime(client, db):
    _, headers = register_user(client, age=13)
    response = client.get("/api/goal", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "targetHours": 10,
        "bedtime": DEFAULT_BEDTIME,
        "healthyRange": {"min": 9, "max": 11},
        "isDefault": True,
    }
    assert db.query(SleepGoal).count() == 0


def test_put_valid_goal_persists_and_publishes_event(client, db):
    user, headers = register_user(client)
    published = []
    clear_subscribers()

    def handle_goal_updated(event, event_db):
        stored = event_db.get(SleepGoal, user["id"])
        published.append((event, stored is not None))

    subscribe(SleepGoalUpdated, handle_goal_updated)
    response = client.put(
        "/api/goal",
        headers=headers,
        json={
            "targetHours": 8.5,
            "bedtime": "22:30",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "targetHours": 8.5,
        "bedtime": "22:30",
        "healthyRange": {"min": 7, "max": 9},
        "isDefault": False,
    }
    assert db.get(SleepGoal, user["id"]).target_hours == 8.5
    assert len(published) == 1
    event, persisted_before_publish = published[0]
    assert isinstance(event, SleepGoalUpdated)
    assert event.user_id == user["id"]
    assert event.target_hours == 8.5
    assert event.bedtime == "22:30"
    assert persisted_before_publish
    clear_subscribers()


def test_out_of_range_target_requires_confirmation(client):
    _, headers = register_user(client, age=30)
    without_confirmation = client.put(
        "/api/goal",
        headers=headers,
        json={"targetHours": 10, "bedtime": "22:30"},
    )
    assert without_confirmation.status_code == 422
    assert without_confirmation.json()["code"] == "TARGET_OUT_OF_RANGE"
    assert "7–9" in without_confirmation.json()["detail"]

    confirmed = client.put(
        "/api/goal",
        headers=headers,
        json={
            "targetHours": 10,
            "bedtime": "22:30",
            "confirmOutOfRange": True,
        },
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["targetHours"] == 10
    assert confirmed.json()["isDefault"] is False


@pytest.mark.parametrize("bedtime", ["24:60", "7:00"])
def test_bedtime_must_be_valid_24_hour_hhmm(client, bedtime):
    _, headers = register_user(client)
    response = client.put(
        "/api/goal",
        headers=headers,
        json={"targetHours": 8, "bedtime": bedtime},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("target", [3.99, 12.01])
def test_target_must_be_between_four_and_twelve(client, target):
    _, headers = register_user(client)
    response = client.put(
        "/api/goal",
        headers=headers,
        json={"targetHours": target, "bedtime": "22:30"},
    )
    assert response.status_code == 422


def test_goals_are_isolated_between_users(client):
    user_a, headers_a = register_user(client, "a-goal@example.com", age=30)
    _, headers_b = register_user(client, "b-goal@example.com", age=65)

    updated = client.put(
        "/api/goal",
        headers=headers_a,
        json={"targetHours": 9, "bedtime": "21:45"},
    )
    assert updated.status_code == 200

    goal_b = client.get("/api/goal", headers=headers_b)
    assert goal_b.status_code == 200
    assert goal_b.json()["targetHours"] == 7.5
    assert goal_b.json()["bedtime"] == DEFAULT_BEDTIME
    assert goal_b.json()["isDefault"] is True
    assert client.get("/api/goal", headers=headers_a).json()["targetHours"] == 9
    assert user_a["id"] != db_user_id(headers_b, client)


def db_user_id(headers, client):
    return client.get("/api/me", headers=headers).json()["id"]


def test_age_change_recalculates_only_default_goal(client, db):
    user, headers = register_user(client, age=13)
    initial = client.get("/api/goal", headers=headers).json()
    assert initial["targetHours"] == 10

    changed_age = client.patch(
        "/api/me",
        headers=headers,
        json={"age": 18},
    )
    assert changed_age.status_code == 200
    updated_default = client.get("/api/goal", headers=headers).json()
    assert updated_default["targetHours"] == 8
    assert updated_default["healthyRange"] == {"min": 7, "max": 9}
    assert updated_default["isDefault"] is True

    client.put(
        "/api/goal",
        headers=headers,
        json={"targetHours": 8.5, "bedtime": "22:00"},
    )
    client.patch("/api/me", headers=headers, json={"age": 65})
    custom_after_age_change = client.get("/api/goal", headers=headers).json()
    assert custom_after_age_change["targetHours"] == 8.5
    assert custom_after_age_change["healthyRange"] == {"min": 7, "max": 8}
    assert custom_after_age_change["isDefault"] is False
    assert user["age"] == 13
    assert db.get(User, user["id"]).age == 65
