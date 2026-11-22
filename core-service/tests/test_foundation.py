from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import Query
from pydantic import ValidationError
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, select

from app.config import Settings, parse_api_keys, settings
from app.database import UTCDateTime, configure_sqlite_engine
from app.errors import AppError
from app.events import (
    SleepGoalUpdated,
    SleepSessionRecorded,
    clear_subscribers,
    publish,
    subscribe,
)
from app.main import app
from app.security import (
    DUMMY_HASH,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_api_key,
    verify_password,
)


@app.get("/api/test-validation")
def validation_probe(value: int = Query(..., gt=0)):
    return {"value": value}


@app.get("/api/test-error")
def app_error_probe():
    raise AppError(409, "TEST_CONFLICT", "Konflik uji.")


@app.get("/api/test-crash")
def crash_probe():
    raise RuntimeError("internal detail must not be exposed")


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_error_response_formats(client):
    not_found = client.get("/api/not-found")
    assert not_found.status_code == 404
    assert not_found.json()["code"] == "NOT_FOUND"
    assert set(not_found.json()) == {"code", "detail"}

    invalid = client.get("/api/test-validation?value=0")
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "VALIDATION_ERROR"
    assert invalid.json()["detail"]["fields"][0]["field"] == "value"
    assert set(invalid.json()) == {"code", "detail"}

    internal = client.get("/api/test-crash")
    assert internal.status_code == 500
    assert internal.json() == {
        "code": "INTERNAL_ERROR",
        "detail": "Terjadi kesalahan internal.",
    }

    app_error = client.get("/api/test-error")
    assert app_error.status_code == 409
    assert app_error.json() == {
        "code": "TEST_CONFLICT",
        "detail": "Konflik uji.",
    }


def test_jwt_roundtrip_and_expiration(monkeypatch):
    token, expires_in = create_access_token("user-123")
    assert expires_in == settings.jwt_expire_minutes * 60
    assert decode_access_token(token)["sub"] == "user-123"

    monkeypatch.setattr(settings, "jwt_expire_minutes", -1)
    expired, _ = create_access_token("user-123")
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired)


def test_jwt_rejects_manipulated_token():
    token, _ = create_access_token("user-123")
    header, payload, signature = token.split(".")
    replacement = "A" if signature[0] != "A" else "B"
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(f"{header}.{payload}.{replacement}{signature[1:]}")


def test_api_key_verification(monkeypatch):
    monkeypatch.setattr(settings, "api_keys", "team-a:key-one,team-b:key-two")
    assert parse_api_keys() == {"team-a": "key-one", "team-b": "key-two"}
    assert verify_api_key("key-two") == "team-b"
    assert verify_api_key("wrong-key") is None
    assert verify_api_key("") is None
    assert verify_api_key(None) is None


def test_password_hashing():
    password_hash = hash_password("correct horse battery staple")
    assert password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("incorrect", password_hash)
    assert not verify_password("incorrect", DUMMY_HASH)


def test_events_publish_and_subscribe():
    clear_subscribers()
    received = []
    subscribe(SleepGoalUpdated, lambda event, db: received.append((event, db)))
    event = SleepGoalUpdated("user-1", 8, "22:30")
    publish(event, None)
    assert received == [(event, None)]

    def failing_handler(_event, _db):
        raise RuntimeError("handler failure")

    subscribe(SleepSessionRecorded, failing_handler)
    subscribe(SleepSessionRecorded, lambda value, _db: received.append((value, None)))
    session_event = SleepSessionRecorded("user-1", "session-1", "created")
    publish(session_event, None)
    assert received[-1] == (session_event, None)
    clear_subscribers()


@pytest.mark.parametrize(
    ("secret", "message"),
    [
        ("", "wajib diisi"),
        ("short", "minimal 32 karakter"),
        ("x" * 27 + "GANTI" + "x" * 10, "GANTI"),
    ],
)
def test_config_rejects_invalid_jwt_secret(secret, message):
    with pytest.raises(ValidationError) as error:
        Settings(jwt_secret=secret)
    assert message in str(error.value)


def test_config_defaults():
    configured = Settings(jwt_secret="valid-test-secret-" + "x" * 32)
    assert configured.timezone == "Asia/Jakarta"
    assert configured.jwt_algorithm == "HS256"
    assert configured.aggregate_min_users == 5


def test_utc_datetime_roundtrip(db):
    metadata = MetaData()
    records = Table(
        "utc_datetime_test",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("value", UTCDateTime()),
    )
    bind = db.get_bind()
    configure_sqlite_engine(bind)
    metadata.create_all(bind=bind)

    original = datetime(2026, 11, 22, 10, 0, tzinfo=timezone(timedelta(hours=7)))
    with bind.begin() as connection:
        connection.execute(records.insert().values(value=original))
        restored = connection.execute(select(records.c.value)).scalar_one()

    assert restored == original.astimezone(timezone.utc)
    assert restored.tzinfo is not None
    assert restored.utcoffset() == timedelta(0)


def test_sqlite_pragmas(tmp_path):
    test_engine = create_engine(f"sqlite:///{tmp_path / 'pragmas.db'}")
    configure_sqlite_engine(test_engine)
    with test_engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
        assert connection.exec_driver_sql("PRAGMA journal_mode").scalar_one() == "wal"
    test_engine.dispose()
