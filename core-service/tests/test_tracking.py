from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.config import settings
from app.events import SleepSessionRecorded, clear_subscribers, subscribe
from app.security import create_access_token
from app.tracking.models import SleepSession


def create_user(client, email="tracking@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Tracker",
            "email": email,
            "password": "tracking-safe-password",
            "age": 25,
        },
    )
    assert response.status_code == 201
    return response.json()


def session_payload(
    start_at="2026-11-20T22:00:00+07:00",
    end_at="2026-11-21T06:00:00+07:00",
    **overrides,
):
    return {
        "startAt": start_at,
        "endAt": end_at,
        "quality": 4,
        "stress": "Sedang",
        "caffeine": 2,
        "screenMinutes": 30,
        "notes": "Terbangun sekali.",
        **overrides,
    }


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_session(client, token, **payload_overrides):
    return client.post(
        "/api/sleep-sessions",
        json=session_payload(**payload_overrides),
        headers=auth_headers(token),
    )


def test_sleep_session_crud_and_event_publication(client, db):
    account = create_user(client)
    token = account["accessToken"]
    published = []
    clear_subscribers()
    subscribe(
        SleepSessionRecorded,
        lambda event, _db: published.append((event.user_id, event.session_id, event.action)),
    )

    created = create_session(client, token)
    assert created.status_code == 201
    body = created.json()
    assert body["id"]
    assert body["userId"] == account["user"]["id"]
    assert body["durationMinutes"] == 480
    assert body["startAt"].endswith("Z")
    assert datetime.fromisoformat(body["startAt"].replace("Z", "+00:00")).utcoffset() == timedelta(0)
    assert body["stress"] == "Sedang"
    assert body["caffeine"] == 2
    assert body["screenMinutes"] == 30
    assert "password_hash" not in created.text

    session_id = body["id"]
    fetched = client.get(
        f"/api/sleep-sessions/{session_id}",
        headers=auth_headers(token),
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == session_id

    updated = client.put(
        f"/api/sleep-sessions/{session_id}",
        json=session_payload(
            start_at="2026-11-20T22:30:00+07:00",
            end_at="2026-11-21T06:30:00+07:00",
            quality=5,
            stress="",
            notes=None,
        ),
        headers=auth_headers(token),
    )
    assert updated.status_code == 200
    assert updated.json()["quality"] == 5
    assert updated.json()["stress"] is None
    assert updated.json()["notes"] is None
    assert updated.json()["durationMinutes"] == 480

    deleted = client.delete(
        f"/api/sleep-sessions/{session_id}",
        headers=auth_headers(token),
    )
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(
        f"/api/sleep-sessions/{session_id}",
        headers=auth_headers(token),
    ).status_code == 404

    assert [action for _, _, action in published] == ["create", "update", "delete"]
    assert all(user_id == account["user"]["id"] for user_id, _, _ in published)
    assert all(session_id == body["id"] for _, session_id, _ in published)
    clear_subscribers()
    assert db.query(SleepSession).count() == 0


@pytest.mark.parametrize(
    ("start_at", "end_at", "error_code"),
    [
        ("2026-11-21T06:00:00+07:00", "2026-11-21T06:00:00+07:00", "INVALID_TIME_RANGE"),
        ("2026-11-21T07:00:00+07:00", "2026-11-21T06:00:00+07:00", "INVALID_TIME_RANGE"),
        ("2026-11-20T13:59:00+07:00", "2026-11-21T06:00:00+07:00", "DURATION_TOO_LONG"),
    ],
)
def test_rejects_invalid_time_ranges(client, start_at, end_at, error_code):
    token = create_user(client)["accessToken"]
    response = create_session(
        client,
        token,
        start_at=start_at,
        end_at=end_at,
    )
    assert response.status_code == 422
    assert response.json()["code"] == error_code


def test_sixteen_hour_session_is_allowed(client):
    token = create_user(client)["accessToken"]
    response = create_session(
        client,
        token,
        start_at="2026-11-20T14:00:00+07:00",
        end_at="2026-11-21T06:00:00+07:00",
    )
    assert response.status_code == 201
    assert response.json()["durationMinutes"] == 960


@pytest.mark.parametrize("quality", [0, 6])
def test_quality_must_be_between_one_and_five(client, quality):
    token = create_user(client)["accessToken"]
    response = create_session(client, token, quality=quality)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_optional_fields_and_limits(client):
    token = create_user(client)["accessToken"]
    response = create_session(
        client,
        token,
        quality=None,
        stress="",
        caffeine=None,
        screenMinutes=None,
        notes="x" * 500,
    )
    assert response.status_code == 201
    assert response.json()["quality"] is None
    assert response.json()["stress"] is None
    assert response.json()["caffeine"] is None
    assert response.json()["screenMinutes"] is None

    too_long = create_session(
        client,
        token,
        start_at="2026-11-22T22:00:00+07:00",
        end_at="2026-11-23T06:00:00+07:00",
        notes="x" * 501,
    )
    assert too_long.status_code == 422

    over_ui_limit = create_session(
        client,
        token,
        start_at="2026-11-24T22:00:00+07:00",
        end_at="2026-11-25T06:00:00+07:00",
        screenMinutes=10000,
    )
    assert over_ui_limit.status_code == 422


def test_overlapping_create_rejected_but_adjacent_session_allowed(client):
    token = create_user(client)["accessToken"]
    first = create_session(client, token)
    assert first.status_code == 201

    overlapping = create_session(
        client,
        token,
        start_at="2026-11-21T05:59:00+07:00",
        end_at="2026-11-21T07:00:00+07:00",
    )
    assert overlapping.status_code == 409
    assert overlapping.json()["code"] == "SESSION_OVERLAP"

    adjacent = create_session(
        client,
        token,
        start_at="2026-11-21T06:00:00+07:00",
        end_at="2026-11-21T07:00:00+07:00",
    )
    assert adjacent.status_code == 201


def test_update_overlap_rejected_and_self_is_excluded(client):
    token = create_user(client)["accessToken"]
    first = create_session(
        client,
        token,
        start_at="2026-11-18T22:00:00+07:00",
        end_at="2026-11-19T06:00:00+07:00",
    ).json()
    second = create_session(
        client,
        token,
        start_at="2026-11-20T22:00:00+07:00",
        end_at="2026-11-21T06:00:00+07:00",
    ).json()

    unchanged = client.put(
        f"/api/sleep-sessions/{second['id']}",
        json=session_payload(
            start_at="2026-11-20T22:00:00+07:00",
            end_at="2026-11-21T06:00:00+07:00",
        ),
        headers=auth_headers(token),
    )
    assert unchanged.status_code == 200

    overlap = client.put(
        f"/api/sleep-sessions/{second['id']}",
        json=session_payload(
            start_at="2026-11-19T05:00:00+07:00",
            end_at="2026-11-19T07:00:00+07:00",
        ),
        headers=auth_headers(token),
    )
    assert overlap.status_code == 409
    assert overlap.json()["code"] == "SESSION_OVERLAP"
    assert client.get(
        f"/api/sleep-sessions/{first['id']}",
        headers=auth_headers(token),
    ).status_code == 200


def test_other_user_cannot_get_update_or_delete_session(client):
    account_a = create_user(client, "a@example.com")
    session = create_session(client, account_a["accessToken"]).json()
    account_b = create_user(client, "b@example.com")
    headers_b = auth_headers(account_b["accessToken"])
    url = f"/api/sleep-sessions/{session['id']}"

    assert client.get(url, headers=headers_b).status_code == 404
    assert client.put(
        url,
        json=session_payload(
            start_at="2026-11-22T22:00:00+07:00",
            end_at="2026-11-23T06:00:00+07:00",
        ),
        headers=headers_b,
    ).status_code == 404
    assert client.delete(url, headers=headers_b).status_code == 404

    assert client.get(
        url,
        headers=auth_headers(account_a["accessToken"]),
    ).status_code == 200


def test_list_filters_local_wake_date_and_paginates(client):
    token = create_user(client)["accessToken"]
    create_session(
        client,
        token,
        start_at="2026-11-19T22:00:00+07:00",
        end_at="2026-11-20T06:00:00+07:00",
    )
    create_session(
        client,
        token,
        start_at="2026-11-20T22:00:00+07:00",
        end_at="2026-11-21T06:00:00+07:00",
    )
    create_session(
        client,
        token,
        start_at="2026-11-21T22:00:00+07:00",
        end_at="2026-11-22T06:00:00+07:00",
    )

    response = client.get(
        "/api/sleep-sessions?from=2026-11-21&to=2026-11-22&limit=1&offset=0",
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 1
    assert body["offset"] == 0
    assert len(body["items"]) == 1
    wake_date = datetime.fromisoformat(
        body["items"][0]["endAt"].replace("Z", "+00:00")
    ).astimezone(ZoneInfo(settings.timezone)).date()
    assert wake_date.isoformat() == "2026-11-22"

    second_page = client.get(
        "/api/sleep-sessions?from=2026-11-21&to=2026-11-22&limit=1&offset=1",
        headers=auth_headers(token),
    )
    assert second_page.status_code == 200
    assert second_page.json()["total"] == 2
    assert len(second_page.json()["items"]) == 1
    assert body["items"][0]["startAt"] > second_page.json()["items"][0]["startAt"]


def test_list_rejects_invalid_date_range_and_limit_over_100(client):
    token = create_user(client)["accessToken"]
    headers = auth_headers(token)
    invalid_range = client.get(
        "/api/sleep-sessions?from=2026-11-22&to=2026-11-21",
        headers=headers,
    )
    assert invalid_range.status_code == 422
    assert invalid_range.json()["code"] == "INVALID_DATE_RANGE"

    too_many = client.get(
        "/api/sleep-sessions?limit=101",
        headers=headers,
    )
    assert too_many.status_code == 422
