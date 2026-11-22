from datetime import datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from app.goals.models import RecommendationCompletion
from app.goals.recommendations import build_recommendations


GOAL = SimpleNamespace(bedtime="23:00")


@pytest.mark.parametrize(
    ("pattern_type", "recommendation_id", "shift"),
    [
        ("late_night_repeat", "shift_bedtime_earlier", -30),
        ("sleep_debt", "sleep_30_minutes_more", -30),
        ("inconsistent_schedule", "consistent_bedtime_window", 0),
    ],
)
def test_each_pattern_produces_its_recommendation(pattern_type, recommendation_id, shift):
    recommendations = build_recommendations(
        {
            "patterns_available": True,
            "patterns": [
                SimpleNamespace(type=pattern_type, severity="warning"),
            ],
        },
        GOAL,
    )

    assert recommendations[0]["id"] == recommendation_id
    assert recommendations[0]["shiftMinutes"] == shift
    assert recommendations[0]["basedOn"] == pattern_type
    assert recommendations[0]["done"] is False
    assert abs(recommendations[0]["shiftMinutes"]) <= 30


def test_recommendations_prioritize_severity_and_never_exceed_three():
    recommendations = build_recommendations(
        {
            "patterns_available": True,
            "patterns": [
                SimpleNamespace(type="late_night_repeat", severity="info"),
                SimpleNamespace(type="inconsistent_schedule", severity="warning"),
                SimpleNamespace(type="sleep_debt", severity="warning"),
            ],
        },
        GOAL,
    )

    assert [item["id"] for item in recommendations] == [
        "consistent_bedtime_window",
        "sleep_30_minutes_more",
        "shift_bedtime_earlier",
    ]
    assert all(abs(item["shiftMinutes"]) <= 30 for item in recommendations)


@pytest.mark.parametrize(
    "patterns",
    [
        None,
        {"patterns_available": False, "patterns": []},
        {"patterns_available": True, "patterns": []},
    ],
)
def test_missing_or_unavailable_patterns_return_general_recommendations(patterns):
    recommendations = build_recommendations(patterns, GOAL)

    assert [item["id"] for item in recommendations] == [
        "track_sleep_3_nights",
        "keep_bedtime_regular",
    ]
    assert all(item["basedOn"] == "general" for item in recommendations)


def register_user(client, email):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Recommendation User",
            "email": email,
            "password": "recommendation-test-password",
            "age": 30,
        },
    )
    assert response.status_code == 201
    body = response.json()
    return {"Authorization": f"Bearer {body['accessToken']}"}


def test_recommendations_endpoint_and_completion_are_idempotent_and_isolated(
    client,
    db,
):
    headers_a = register_user(client, "recommendation-a@example.com")
    headers_b = register_user(client, "recommendation-b@example.com")

    response = client.get("/api/recommendations", headers=headers_a)
    assert response.status_code == 200
    assert response.json()["basedOnPatterns"] == []
    assert response.json()["items"][0]["id"] == "track_sleep_3_nights"

    url = "/api/recommendations/track_sleep_3_nights/complete"
    assert client.post(url, headers=headers_a).json() == {
        "id": "track_sleep_3_nights",
        "done": True,
    }
    assert client.post(url, headers=headers_a).status_code == 200
    assert db.query(RecommendationCompletion).count() == 1

    done_items = client.get("/api/recommendations", headers=headers_a).json()["items"]
    other_user_items = client.get(
        "/api/recommendations",
        headers=headers_b,
    ).json()["items"]
    assert next(item for item in done_items if item["id"] == "track_sleep_3_nights")[
        "done"
    ]
    assert not next(
        item for item in other_user_items if item["id"] == "track_sleep_3_nights"
    )["done"]

    unknown = client.post(
        "/api/recommendations/not-a-recommendation/complete",
        headers=headers_a,
    )
    assert unknown.status_code == 404
    assert unknown.json()["code"] == "RECOMMENDATION_NOT_FOUND"


def test_recommendations_endpoint_uses_analysis_patterns(client):
    headers = register_user(client, "recommendation-pattern@example.com")
    today = datetime.now(ZoneInfo("Asia/Jakarta")).date()
    for days_ago in (0, 1, 2):
        bedtime_date = today - timedelta(days=days_ago)
        response = client.post(
            "/api/sleep-sessions",
            headers=headers,
            json={
                "startAt": f"{bedtime_date.isoformat()}T02:00:00+07:00",
                "endAt": f"{bedtime_date.isoformat()}T10:00:00+07:00",
            },
        )
        assert response.status_code == 201

    recommendations = client.get(
        "/api/recommendations",
        headers=headers,
    )
    assert recommendations.status_code == 200
    body = recommendations.json()
    assert body["basedOnPatterns"] == ["late_night_repeat"]
    assert body["items"][0]["id"] == "shift_bedtime_earlier"
    assert body["items"][0]["basedOn"] == "late_night_repeat"
