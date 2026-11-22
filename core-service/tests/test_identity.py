from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import settings
from app.identity.models import User
from app.security import create_access_token


def register_payload(**overrides):
    payload = {
        "name": "Nara",
        "email": "Nara@example.com",
        "password": "sleep-safe-password",
        "age": 21,
        "city": "Bandung",
    }
    return {**payload, **overrides}


def register(client, **overrides):
    return client.post("/api/auth/register", json=register_payload(**overrides))


def test_register_creates_user_and_returns_token(client, db):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["accessToken"]
    assert body["tokenType"] == "bearer"
    assert body["expiresIn"] == settings.jwt_expire_minutes * 60
    assert body["user"] == {
        "id": body["user"]["id"],
        "name": "Nara",
        "email": "nara@example.com",
        "age": 21,
        "city": "Bandung",
    }
    assert "password_hash" not in response.text
    assert db.query(User).one().email == "nara@example.com"


def test_duplicate_email_is_case_insensitive(client):
    assert register(client).status_code == 201
    response = register(client, email="NARA@EXAMPLE.COM")
    assert response.status_code == 409
    assert response.json()["code"] == "EMAIL_TAKEN"


@pytest.mark.parametrize(
    "password",
    [
        "short7",
        "x" * 73,
    ],
)
def test_register_rejects_password_outside_utf8_byte_limits(client, password):
    response = register(client, password=password)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_register_validates_password_by_utf8_bytes(client):
    response = register(client, password="é" * 4)
    assert response.status_code == 201


@pytest.mark.parametrize("age", [9, 121])
def test_register_rejects_age_outside_range(client, age):
    response = register(client, age=age)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_login_success_and_invalid_credentials_share_message(client):
    assert register(client).status_code == 201
    success = client.post(
        "/api/auth/login",
        json={"email": "NARA@example.com", "password": "sleep-safe-password"},
    )
    assert success.status_code == 200
    assert success.json()["user"]["email"] == "nara@example.com"
    assert "password_hash" not in success.text

    wrong_password = client.post(
        "/api/auth/login",
        json={"email": "nara@example.com", "password": "wrong-password"},
    )
    missing_email = client.post(
        "/api/auth/login",
        json={"email": "missing@example.com", "password": "wrong-password"},
    )
    assert wrong_password.status_code == missing_email.status_code == 401
    assert wrong_password.json() == missing_email.json()
    assert wrong_password.json()["code"] == "INVALID_CREDENTIALS"


def test_me_requires_and_validates_token(client):
    missing = client.get("/api/me")
    assert missing.status_code == 401
    assert missing.json()["code"] == "NOT_AUTHENTICATED"
    assert client.get(
        "/api/me", headers={"Authorization": "Bearer not-a-token"}
    ).json()["code"] == "INVALID_TOKEN"

    registration = register(client).json()
    user_id = registration["user"]["id"]
    expired = jwt.encode(
        {
            "sub": user_id,
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    response = client.get(
        "/api/me",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"

    deleted_user_token, _ = create_access_token("deleted-user-id")
    deleted_user = client.get(
        "/api/me",
        headers={"Authorization": f"Bearer {deleted_user_token}"},
    )
    assert deleted_user.status_code == 401
    assert deleted_user.json()["code"] == "INVALID_TOKEN"


def test_me_get_and_patch_partial_fields_and_clear_city(client):
    registered = register(client).json()
    headers = {"Authorization": f"Bearer {registered['accessToken']}"}

    me = client.get("/api/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "nara@example.com"
    assert "password_hash" not in me.text

    updated = client.patch("/api/me", json={"age": 22}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["age"] == 22
    assert updated.json()["name"] == "Nara"
    assert updated.json()["city"] == "Bandung"
    assert "password_hash" not in updated.text

    email_update = client.patch(
        "/api/me",
        json={"name": "Nara Baru", "email": "new@example.com"},
        headers=headers,
    )
    assert email_update.status_code == 422

    cleared = client.patch("/api/me", json={"city": None}, headers=headers)
    assert cleared.status_code == 200
    assert cleared.json()["city"] is None
    assert cleared.json()["email"] == "nara@example.com"
    assert cleared.json()["name"] == "Nara"
    assert "password_hash" not in cleared.text


def test_user_update_requires_at_least_one_field(client):
    registered = register(client).json()
    headers = {"Authorization": f"Bearer {registered['accessToken']}"}
    response = client.patch("/api/me", json={}, headers=headers)
    assert response.status_code == 422
