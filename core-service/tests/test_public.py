from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import settings


def register_user(client, email, city):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Aggregate User",
            "email": email,
            "password": "public-aggregate-test-password",
            "age": 30,
            "city": city,
        },
    )
    assert response.status_code == 201
    body = response.json()
    return {"Authorization": f"Bearer {body['accessToken']}"}


def add_session(client, headers, target_date, quality, slot=0):
    starts = ("02:00", "14:00")
    ends = ("10:00", "22:00")
    start_date = target_date.isoformat()
    response = client.post(
        "/api/sleep-sessions",
        headers=headers,
        json={
            "startAt": f"{start_date}T{starts[slot]}:00+07:00",
            "endAt": f"{start_date}T{ends[slot]}:00+07:00",
            "quality": quality,
        },
    )
    assert response.status_code == 201


def seed_user(client, email, city, target_date, qualities):
    headers = register_user(client, email, city)
    for slot, quality in enumerate(qualities):
        add_session(client, headers, target_date, quality, slot)
    return headers


def configure_api_key(monkeypatch):
    monkeypatch.setattr(settings, "api_keys", "analytics-group:correct-secret-key")
    return {"X-API-Key": "correct-secret-key"}


def test_public_api_key_errors_and_authentication_are_separate(client, monkeypatch):
    configure_api_key(monkeypatch)

    missing = client.get("/api/public/aggregate/score?city=Jakarta")
    assert missing.status_code == 401
    assert missing.json()["code"] == "MISSING_API_KEY"

    wrong = client.get(
        "/api/public/aggregate/score?city=Jakarta",
        headers={"X-API-Key": "wrong-one"},
    )
    another_wrong = client.get(
        "/api/public/aggregate/score?city=Jakarta",
        headers={"X-API-Key": "wrong-two"},
    )
    assert wrong.status_code == another_wrong.status_code == 401
    assert wrong.json()["code"] == another_wrong.json()["code"] == "INVALID_API_KEY"
    assert wrong.json()["detail"] == another_wrong.json()["detail"]

    token_response = client.post(
        "/api/auth/register",
        json={
            "name": "JWT Caller",
            "email": "jwt-public@example.com",
            "password": "jwt-public-test-password",
            "age": 30,
        },
    )
    token = token_response.json()["accessToken"]
    public_with_jwt_only = client.get(
        "/api/public/aggregate/daily",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert public_with_jwt_only.status_code == 401
    assert public_with_jwt_only.json()["code"] == "MISSING_API_KEY"

    private_with_api_key_only = client.get(
        "/api/me",
        headers={"X-API-Key": "correct-secret-key"},
    )
    assert private_with_api_key_only.status_code == 401


def test_city_aggregate_threshold_casefold_and_per_user_average(
    client,
    monkeypatch,
    caplog,
):
    api_headers = configure_api_key(monkeypatch)
    target_date = datetime.now(ZoneInfo(settings.timezone)).date() - timedelta(days=1)
    seed_user(
        client,
        "aggregate-one@example.com",
        "JAKARTA",
        target_date,
        [1, 5],
    )
    seed_user(
        client,
        "aggregate-two@example.com",
        "Jakarta",
        target_date,
        [2],
    )
    seed_user(
        client,
        "aggregate-three@example.com",
        "jaKarta",
        target_date,
        [3],
    )
    seed_user(
        client,
        "aggregate-four@example.com",
        "Jakarta",
        target_date,
        [4],
    )

    url = f"/api/public/aggregate/score?city=jAkArTa&date={target_date.isoformat()}"
    insufficient = client.get(url, headers=api_headers)
    assert insufficient.status_code == 404
    assert insufficient.json()["code"] == "NOT_ENOUGH_DATA"
    assert "4" not in insufficient.json()["detail"]

    seed_user(
        client,
        "aggregate-five@example.com",
        "Jakarta",
        target_date,
        [5],
    )
    caplog.set_level("INFO")
    aggregate = client.get(url, headers=api_headers)

    assert aggregate.status_code == 200
    assert set(aggregate.json()) == {"city", "date", "averageScore", "sampleSize"}
    assert aggregate.json() == {
        "city": "jAkArTa",
        "date": target_date.isoformat(),
        "averageScore": 84.6,
        "sampleSize": 5,
    }
    assert "analytics-group" in caplog.text
    assert "correct-secret-key" not in caplog.text


def test_daily_aggregate_includes_all_cities_and_defaults_to_yesterday(
    client,
    monkeypatch,
):
    api_headers = configure_api_key(monkeypatch)
    target_date = datetime.now(ZoneInfo(settings.timezone)).date() - timedelta(days=1)
    seed_user(
        client,
        "daily-one@example.com",
        "Jakarta",
        target_date,
        [1, 5],
    )
    seed_user(client, "daily-two@example.com", "Jakarta", target_date, [2])
    seed_user(client, "daily-three@example.com", "Jakarta", target_date, [3])
    seed_user(client, "daily-four@example.com", "Jakarta", target_date, [4])
    seed_user(client, "daily-five@example.com", "Jakarta", target_date, [5])
    seed_user(client, "daily-six@example.com", "Bandung", target_date, [5])

    response = client.get("/api/public/aggregate/daily", headers=api_headers)

    assert response.status_code == 200
    assert set(response.json()) == {"date", "averageScore", "sampleSize"}
    assert response.json() == {
        "date": target_date.isoformat(),
        "averageScore": 87.2,
        "sampleSize": 6,
    }
