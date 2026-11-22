from datetime import date, datetime, timedelta
from math import isclose
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.environment.models import NightTemperatureCache
from app.environment.openmeteo import (
    USER_AGENT,
    CityLocation,
    OpenMeteoAdapter,
    OpenMeteoError,
)
from app.environment.router import get_openmeteo_adapter
from app.environment.service import pearson_correlation
from app.main import app


LOCAL_TZ = ZoneInfo("Asia/Jakarta")


def register_user(client, email, city="Jakarta"):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Environment User",
            "email": email,
            "password": "environment-test-password",
            "age": 30,
            "city": city,
        },
    )
    assert response.status_code == 201
    body = response.json()
    return body["user"], {"Authorization": f"Bearer {body['accessToken']}"}


def create_sessions(client, headers, count=7, factors=True):
    today = datetime.now(LOCAL_TZ).date()
    for index in range(count):
        wake_date = today - timedelta(days=count - index - 1)
        bedtime_date = wake_date - timedelta(days=1)
        data = {
            "startAt": f"{bedtime_date.isoformat()}T22:00:00+07:00",
            "endAt": f"{wake_date.isoformat()}T06:00:00+07:00",
            "quality": index % 5 + 1,
        }
        if factors:
            data.update({"caffeine": index, "screenMinutes": index * 30})
        response = client.post(
            "/api/sleep-sessions",
            headers=headers,
            json=data,
        )
        assert response.status_code == 201


def forecast_payload(wake_dates):
    first_hour = datetime.combine(min(wake_dates) - timedelta(days=1), datetime.min.time())
    last_hour = datetime.combine(max(wake_dates), datetime.min.time()) + timedelta(
        hours=6
    )
    hours = []
    current = first_hour
    while current <= last_hour:
        hours.append(current)
        current += timedelta(hours=1)
    return {
        "hourly": {
            "time": [hour.isoformat(timespec="minutes") for hour in hours],
            "temperature_2m": [
                20.0 + hour.hour / 10 + hour.day / 100 for hour in hours
            ],
        }
    }


def successful_handler(wake_dates, requests):
    forecast = forecast_payload(wake_dates)

    def handle(request):
        requests.append(request)
        assert request.headers["user-agent"] == USER_AGENT
        if request.url.host == "geocoding-api.open-meteo.com":
            assert request.url.params["count"] == "1"
            assert request.url.params["country_code"] == "ID"
            return httpx.Response(
                200,
                json={
                    "results": [
                        {"latitude": -6.2, "longitude": 106.8, "name": "Jakarta"}
                    ]
                },
            )
        assert request.url.host == "api.open-meteo.com"
        assert request.url.params["hourly"] == "temperature_2m"
        assert request.url.params["past_days"] == "30"
        assert request.url.params["timezone"] == "Asia/Jakarta"
        return httpx.Response(200, json=forecast)

    return handle


def with_adapter(client, adapter, request):
    app.dependency_overrides[get_openmeteo_adapter] = lambda: adapter
    try:
        return request()
    finally:
        app.dependency_overrides.pop(get_openmeteo_adapter, None)


@pytest.mark.parametrize(
    ("pairs", "expected"),
    [
        ([(1, 2), (2, 4), (3, 6)], 1.0),
        ([(1, 6), (2, 4), (3, 2)], -1.0),
    ],
)
def test_pearson_returns_known_perfect_correlations(pairs, expected):
    assert pearson_correlation(pairs) == expected


def test_pearson_returns_none_without_variance_or_enough_pairs():
    assert pearson_correlation([(2, 1), (2, 3)]) is None
    assert pearson_correlation([(1, 4), (2, 4)]) is None
    assert pearson_correlation([(1, 2)]) is None


def test_adapter_averages_local_22_to_06_hours():
    wake_date = date(2026, 11, 22)
    hours = [
        datetime(2026, 11, 21, 21),
        datetime(2026, 11, 21, 22),
        datetime(2026, 11, 21, 23),
        datetime(2026, 11, 22, 0),
        datetime(2026, 11, 22, 1),
        datetime(2026, 11, 22, 2),
        datetime(2026, 11, 22, 3),
        datetime(2026, 11, 22, 4),
        datetime(2026, 11, 22, 5),
        datetime(2026, 11, 22, 6),
    ]
    payload = {
        "hourly": {
            "time": [hour.isoformat(timespec="minutes") for hour in hours],
            "temperature_2m": list(range(10)),
        }
    }
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, json=payload)
        )
    )
    adapter = OpenMeteoAdapter(client)
    try:
        result = adapter.night_temperatures(
            CityLocation("jakarta", -6.2, 106.8),
            {wake_date},
        )
    finally:
        client.close()

    assert len(result) == 1
    assert result[0].date == wake_date
    assert isclose(result[0].avg_c, sum(range(1, 9)) / 8)


def test_environment_success_and_geocoding_and_temperature_cache(client, db):
    user, headers = register_user(client, "environment-cache@example.com")
    create_sessions(client, headers)
    today = datetime.now(LOCAL_TZ).date()
    wake_dates = {today - timedelta(days=offset) for offset in range(7)}
    requests = []
    mock_client = httpx.Client(
        transport=httpx.MockTransport(successful_handler(wake_dates, requests))
    )
    adapter = OpenMeteoAdapter(mock_client)

    first = with_adapter(
        client,
        adapter,
        lambda: client.get("/api/insights/environment", headers=headers),
    )
    second = with_adapter(
        client,
        adapter,
        lambda: client.get("/api/insights/environment", headers=headers),
    )
    mock_client.close()

    assert first.status_code == second.status_code == 200
    body = first.json()
    assert body["available"] is True
    assert body["sampleSize"] == 7
    assert body["minRequired"] == 7
    assert body["temperatureAvailable"] is True
    assert [finding["factor"] for finding in body["findings"]] == [
        "temperature",
        "caffeine",
        "screen",
    ]
    assert body["disclaimer"]
    assert len(requests) == 2
    assert db.get(NightTemperatureCache, ("jakarta", today)) is not None
    assert user["city"] == "Jakarta"


def test_network_failure_falls_back_to_partial_temperature_cache(client, db):
    user, headers = register_user(client, "environment-fallback@example.com")
    create_sessions(client, headers)
    today = datetime.now(LOCAL_TZ).date()
    wake_dates = {today - timedelta(days=offset) for offset in range(7)}

    successful_requests = []
    success_client = httpx.Client(
        transport=httpx.MockTransport(
            successful_handler(wake_dates, successful_requests)
        )
    )
    success_adapter = OpenMeteoAdapter(success_client)
    initial = with_adapter(
        client,
        success_adapter,
        lambda: client.get("/api/insights/environment", headers=headers),
    )
    success_client.close()
    assert initial.status_code == 200

    db.delete(db.get(NightTemperatureCache, ("jakarta", today)))
    db.commit()
    failed_requests = []

    def offline(request):
        failed_requests.append(request)
        raise httpx.ConnectError("offline", request=request)

    offline_client = httpx.Client(transport=httpx.MockTransport(offline))
    offline_adapter = OpenMeteoAdapter(offline_client)
    response = with_adapter(
        client,
        offline_adapter,
        lambda: client.get("/api/insights/environment", headers=headers),
    )
    offline_client.close()

    assert response.status_code == 200
    assert response.json()["temperatureAvailable"] is True
    assert response.json()["sampleSize"] == 7
    assert len(failed_requests) == 2
    assert db.get(NightTemperatureCache, ("jakarta", today)) is None
    assert db.get(NightTemperatureCache, ("jakarta", today - timedelta(days=1)))
    assert user["city"] == "Jakarta"


def test_network_failure_without_cache_returns_unavailable_not_500(client):
    _, headers = register_user(client, "environment-offline@example.com")
    create_sessions(client, headers)
    requests = []

    def offline(request):
        requests.append(request)
        raise httpx.ConnectError("offline", request=request)

    mock_client = httpx.Client(transport=httpx.MockTransport(offline))
    adapter = OpenMeteoAdapter(mock_client)
    response = with_adapter(
        client,
        adapter,
        lambda: client.get("/api/insights/environment", headers=headers),
    )
    mock_client.close()

    assert response.status_code == 200
    assert response.json()["temperatureAvailable"] is False
    assert response.json()["available"] is True
    assert len(requests) == 2


def test_fewer_than_seven_factor_sessions_are_not_available(client):
    _, headers = register_user(
        client,
        "environment-small-sample@example.com",
        city=None,
    )
    create_sessions(client, headers, count=6, factors=True)
    response = client.get("/api/insights/environment", headers=headers)

    assert response.status_code == 200
    assert response.json()["available"] is False
    assert response.json()["sampleSize"] == 6
    assert response.json()["temperatureAvailable"] is False
    assert response.json()["disclaimer"]


def test_user_without_city_gets_environment_response_without_network(client):
    requests = []
    user, headers = register_user(
        client,
        "environment-no-city@example.com",
        city=None,
    )

    def unexpected_network(request):
        requests.append(request)
        raise AssertionError("Tidak seharusnya memanggil jaringan")

    mock_client = httpx.Client(
        transport=httpx.MockTransport(unexpected_network)
    )
    adapter = OpenMeteoAdapter(mock_client)
    response = with_adapter(
        client,
        adapter,
        lambda: client.get("/api/insights/environment", headers=headers),
    )
    mock_client.close()

    assert response.status_code == 200
    assert response.json()["temperatureAvailable"] is False
    assert user["city"] is None
    assert requests == []


def test_changed_geocoding_format_is_handled_as_unavailable(client):
    _, headers = register_user(client, "environment-format@example.com")
    create_sessions(client, headers)

    def changed_format(_request):
        return httpx.Response(200, json={"locations": []})

    mock_client = httpx.Client(transport=httpx.MockTransport(changed_format))
    adapter = OpenMeteoAdapter(mock_client)
    with pytest.raises(OpenMeteoError):
        adapter.geocode("jakarta", "Jakarta")

    response = with_adapter(
        client,
        adapter,
        lambda: client.get("/api/insights/environment", headers=headers),
    )
    mock_client.close()

    assert response.status_code == 200
    assert response.json()["temperatureAvailable"] is False
