from pathlib import Path


def test_openapi_is_valid_and_documents_tags_security_examples_and_errors(client):
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    tags = {tag["name"] for tag in schema["tags"]}
    assert tags == {
        "Identity",
        "Tracking",
        "Goals",
        "Analysis",
        "Reminders",
        "Environment",
        "Public",
        "System",
    }

    schemes = schema["components"]["securitySchemes"]
    assert schemes["BearerAuth"]["scheme"] == "bearer"
    assert schemes["ApiKeyAuth"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
    }
    assert "examples" in schema["components"]["schemas"]["RegisterIn"]
    assert "examples" in schema["components"]["schemas"]["SleepSessionIn"]
    assert "examples" in schema["components"]["schemas"]["CityScoreAggregateOut"]

    for path, path_item in schema["paths"].items():
        if not path.startswith("/api/") or path.startswith("/api/test-"):
            continue
        for operation in path_item.values():
            if not isinstance(operation, dict) or "responses" not in operation:
                continue
            assert operation.get("summary")
            assert operation.get("description")
            if path == "/api/health":
                continue
            assert all(
                status in operation["responses"]
                for status in ("401", "404", "409", "422")
            )
            for status in ("401", "404", "409", "422"):
                error_schema = operation["responses"][status]["content"][
                    "application/json"
                ]["schema"]
                assert error_schema["$ref"].endswith("/ErrorResponse")

    assert schema["paths"]["/api/public/aggregate/score"]["get"]["security"] == [
        {"ApiKeyAuth": []}
    ]
    assert schema["paths"]["/api/me"]["get"]["security"] == [
        {"BearerAuth": []}
    ]
    assert "security" not in schema["paths"]["/api/auth/register"]["post"]
    assert "security" not in schema["paths"]["/api/health"]["get"]


def test_gateway_limits_body_timeouts_and_never_logs_auth_headers():
    repository_root = Path(__file__).resolve().parents[2]
    nginx_config = (repository_root / "gateway" / "nginx.conf").read_text(
        encoding="utf-8"
    )
    assert "client_max_body_size 1m;" in nginx_config
    assert "proxy_connect_timeout 5s;" in nginx_config
    assert "proxy_send_timeout 30s;" in nginx_config
    assert "proxy_read_timeout 30s;" in nginx_config
    assert "$http_authorization" not in nginx_config
    assert "$http_x_api_key" not in nginx_config

    compose_config = (repository_root / "docker-compose.yml").read_text(
        encoding="utf-8"
    )
    assert "healthcheck:" in compose_config
    assert "/api/health" in compose_config

    env_example = (repository_root / ".env.example").read_text(encoding="utf-8")
    assert "SEED_PASSWORD=" in env_example
    assert "TIMEZONE=Asia/Jakarta" in env_example
    assert "AGGREGATE_MIN_USERS=5" in env_example


def test_protected_routes_and_public_routes_reject_missing_credentials(client):
    protected_requests = [
        ("GET", "/api/me", None),
        ("PATCH", "/api/me", {"name": "Nara Baru"}),
        (
            "POST",
            "/api/sleep-sessions",
            {
                "startAt": "2026-11-20T22:30:00+07:00",
                "endAt": "2026-11-21T06:30:00+07:00",
            },
        ),
        ("GET", "/api/sleep-sessions", None),
        ("GET", "/api/sleep-sessions/unknown", None),
        (
            "PUT",
            "/api/sleep-sessions/unknown",
            {
                "startAt": "2026-11-20T22:30:00+07:00",
                "endAt": "2026-11-21T06:30:00+07:00",
            },
        ),
        ("DELETE", "/api/sleep-sessions/unknown", None),
        ("GET", "/api/goal", None),
        (
            "PUT",
            "/api/goal",
            {"targetHours": 8, "bedtime": "22:30"},
        ),
        ("GET", "/api/recommendations", None),
        (
            "POST",
            "/api/recommendations/track_sleep_3_nights/complete",
            None,
        ),
        ("GET", "/api/sleep-score", None),
        ("GET", "/api/patterns", None),
        ("GET", "/api/summary/weekly", None),
        ("GET", "/api/reminders", None),
        ("PUT", "/api/reminders", {"enabled": True}),
        ("GET", "/api/insights/environment", None),
    ]

    for method, path, body in protected_requests:
        response = client.request(method, path, json=body)
        assert response.status_code == 401, (method, path, response.text)

    public_score = client.get("/api/public/aggregate/score?city=Bandung")
    public_daily = client.get("/api/public/aggregate/daily")
    assert public_score.status_code == 401
    assert public_daily.status_code == 401
    assert public_score.json()["code"] == "MISSING_API_KEY"
    assert public_daily.json()["code"] == "MISSING_API_KEY"
