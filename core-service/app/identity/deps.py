from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..database import get_db
from ..errors import AppError
from ..security import decode_access_token
from .models import User


bearer_scheme = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise AppError(401, "NOT_AUTHENTICATED", "Autentikasi diperlukan.")

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError as error:
        raise AppError(401, "INVALID_TOKEN", "Token tidak valid atau kedaluwarsa.") from error

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise AppError(401, "INVALID_TOKEN", "Token tidak valid atau kedaluwarsa.")

    user = db.get(User, subject)
    if user is None:
        raise AppError(401, "INVALID_TOKEN", "Token tidak valid atau kedaluwarsa.")
    return user
