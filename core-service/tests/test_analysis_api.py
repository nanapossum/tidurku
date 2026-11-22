from sqlalchemy import event


def register_user(client, email):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Analysis User",
            "email": email,
            "password": "analysis-safe-password",
            "age": 30,
        },
    )
    assert response.status_code == 201
    body = response.json()
    return body["user"], {"Authorization": f"Bearer {body['accessToken']}"}


def create_session(
    client,
    headers,
    start_at,
    end_at,
    quality=4,
):
    return client.post(
        "/api/sleep-sessions",
        headers=headers,
        json={
            "startAt": start_at,
            "endAt": end_at,
            "quality": quality,
        },
    )


def test_analysis_endpoints_with_seeded_sessions_and_score_in_tracking(client):
    _, headers = register_user(client, "analysis@example.com")
    for day in (17, 18, 19, 20):
        created = create_session(
            client,
            headers,
            f"2026-11-{day - 1:02d}T22:00:00+07:00",
            f"2026-11-{day:02d}T06:00:00+07:00",
        )
        assert created.status_code == 201
        assert isinstance(created.json()["score"], int)

    score = client.get("/api/sleep-score", headers=headers)
    assert score.status_code == 200
    score_body = score.json()
    assert score_body["sessionCount"] == 4
    assert score_body["latest"]["sessionId"]
    assert isinstance(score_body["latest"]["score"], int)
    assert score_body["latest"]["breakdown"]["consistencyScore"] is not None
    assert score_body["weeklyAverage"] is not None

    patterns = client.get("/api/patterns", headers=headers)
    assert patterns.status_code == 200
    assert patterns.json()["patternsAvailable"] is True
    assert patterns.json()["minSessions"] == 3
    assert patterns.json()["sleepDebtMinutes"] == 0
    assert patterns.json()["debtWarning"] is False

    summary = client.get(
        "/api/summary/weekly?weekStart=2026-11-16",
        headers=headers,
    )
    assert summary.status_code == 200
    summary_body = summary.json()
    assert summary_body["weekStart"] == "2026-11-16"
    assert len(summary_body["days"]) == 7
    assert summary_body["days"][0]["sessionCount"] == 0
    assert summary_body["days"][1]["sessionCount"] == 1
    assert summary_body["days"][1]["durationMinutes"] == 480
    assert summary_body["days"][1]["metGoal"] is True
    assert summary_body["days"][0]["durationMinutes"] is None
    assert summary_body["daysMeetingGoal"] == 4

    sessions = client.get("/api/sleep-sessions", headers=headers)
    assert sessions.status_code == 200
    assert all(isinstance(item["score"], int) for item in sessions.json()["items"])


def test_analysis_endpoints_are_isolated_by_user(client):
    _, user_a_headers = register_user(client, "analysis-a@example.com")
    create_session(
        client,
        user_a_headers,
        "2026-11-19T22:00:00+07:00",
        "2026-11-20T06:00:00+07:00",
    )
    _, user_b_headers = register_user(client, "analysis-b@example.com")

    score = client.get("/api/sleep-score", headers=user_b_headers).json()
    assert score["latest"] is None
    assert score["weeklyAverage"] is None
    assert score["sessionCount"] == 0

    patterns = client.get("/api/patterns", headers=user_b_headers).json()
    assert patterns["patternsAvailable"] is False
    assert patterns["patterns"] == []
    assert patterns["sleepDebtMinutes"] == 0

    summary = client.get(
        "/api/summary/weekly?weekStart=2026-11-16",
        headers=user_b_headers,
    ).json()
    assert summary["daysMeetingGoal"] == 0
    assert all(day["sessionCount"] == 0 for day in summary["days"])


def test_tracking_page_scores_without_per_session_queries(client, db):
    _, headers = register_user(client, "score-page@example.com")
    for day in (17, 18, 19, 20):
        create_session(
            client,
            headers,
            f"2026-11-{day - 1:02d}T22:00:00+07:00",
            f"2026-11-{day:02d}T06:00:00+07:00",
        )

    session_queries = []

    def count_session_queries(_conn, _cursor, statement, _params, _context, _many):
        if "sleep_sessions" in statement.lower():
            session_queries.append(statement)

    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", count_session_queries)
    try:
        response = client.get("/api/sleep-sessions", headers=headers)
    finally:
        event.remove(engine, "before_cursor_execute", count_session_queries)

    assert response.status_code == 200
    assert len(response.json()["items"]) == 4
    assert len(session_queries) == 3


def test_analysis_endpoints_require_authentication(client):
    assert client.get("/api/sleep-score").status_code == 401
    assert client.get("/api/patterns").status_code == 401
    assert client.get("/api/summary/weekly").status_code == 401
