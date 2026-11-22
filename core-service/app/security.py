import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from hmac import compare_digest

from .config import parse_api_keys, settings


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("ascii"),
    )


DUMMY_HASH = hash_password("tidurku-dummy-password")


def create_access_token(sub: str) -> tuple[str, int]:
    expires_in = settings.jwt_expire_minutes * 60
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    token = jwt.encode(
        {"sub": sub, "exp": expires_at},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return token, expires_in


def decode_access_token(token: str) -> dict[str, object]:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )


def verify_api_key(nilai_header: str | None) -> str | None:
    candidate = (nilai_header or "").encode("utf-8")
    matched_group: str | None = None
    for group, key in parse_api_keys().items():
        is_match = compare_digest(candidate, key.encode("utf-8"))
        if is_match and matched_group is None:
            matched_group = group
    return matched_group
