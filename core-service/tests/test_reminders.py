from app.reminders.models import ReminderSetting
from app.reminders.service import reminder_time_for_bedtime


def register_user(client, email):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Reminder User",
            "email": email,
            "password": "reminder-test-password",
            "age": 30,
        },
    )
    assert response.status_code == 201
    body = response.json()
    return body["user"], {"Authorization": f"Bearer {body['accessToken']}"}


def test_reminder_default_follows_goal_bedtime(client):
    _, headers = register_user(client, "reminder-default@example.com")

    response = client.get("/api/reminders", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "enabled": True,
        "time": "22:30",
        "isCustom": False,
    }


def test_custom_reminder_can_be_reset_to_default_and_omission_preserves_it(
    client,
    db,
):
    user, headers = register_user(client, "reminder-custom@example.com")

    custom = client.put(
        "/api/reminders",
        headers=headers,
        json={"enabled": False, "time": "21:15"},
    )
    assert custom.status_code == 200
    assert custom.json() == {
        "enabled": False,
        "time": "21:15",
        "isCustom": True,
    }

    preserved = client.put(
        "/api/reminders",
        headers=headers,
        json={"enabled": True},
    )
    assert preserved.json()["time"] == "21:15"
    assert preserved.json()["isCustom"] is True

    reset = client.put(
        "/api/reminders",
        headers=headers,
        json={"enabled": True, "time": None},
    )
    assert reset.json() == {
        "enabled": True,
        "time": "22:30",
        "isCustom": False,
    }
    setting = db.get(ReminderSetting, user["id"])
    assert setting.time == "22:30"
    assert setting.is_custom is False


def test_goal_update_refreshes_default_time_but_preserves_custom_time(client, db):
    user, default_headers = register_user(client, "reminder-goal@example.com")
    client.put(
        "/api/reminders",
        headers=default_headers,
        json={"enabled": True, "time": None},
    )
    changed_goal = client.put(
        "/api/goal",
        headers=default_headers,
        json={"targetHours": 8, "bedtime": "00:15"},
    )
    assert changed_goal.status_code == 200
    assert db.get(ReminderSetting, user["id"]).time == "23:45"
    assert client.get("/api/reminders", headers=default_headers).json()["time"] == "23:45"

    user_custom, custom_headers = register_user(client, "reminder-custom-goal@example.com")
    client.put(
        "/api/reminders",
        headers=custom_headers,
        json={"enabled": True, "time": "20:45"},
    )
    client.put(
        "/api/goal",
        headers=custom_headers,
        json={"targetHours": 8, "bedtime": "22:00"},
    )
    custom_setting = db.get(ReminderSetting, user_custom["id"])
    assert custom_setting.time == "20:45"
    assert custom_setting.is_custom is True


def test_reminder_settings_are_isolated_between_users(client):
    _, headers_a = register_user(client, "reminder-a@example.com")
    _, headers_b = register_user(client, "reminder-b@example.com")
    client.put(
        "/api/reminders",
        headers=headers_a,
        json={"enabled": False, "time": "20:00"},
    )

    assert client.get("/api/reminders", headers=headers_a).json() == {
        "enabled": False,
        "time": "20:00",
        "isCustom": True,
    }
    assert client.get("/api/reminders", headers=headers_b).json() == {
        "enabled": True,
        "time": "22:30",
        "isCustom": False,
    }


def test_default_time_wraps_at_midnight_and_invalid_time_is_rejected(client):
    assert reminder_time_for_bedtime("00:15") == "23:45"
    _, headers = register_user(client, "reminder-invalid@example.com")
    response = client.put(
        "/api/reminders",
        headers=headers,
        json={"enabled": True, "time": "24:00"},
    )
    assert response.status_code == 422
