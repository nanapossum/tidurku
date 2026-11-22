from typing import Annotated

from fastapi import Security
from fastapi.security import APIKeyHeader

from ..errors import AppError
from ..security import verify_api_key


api_key_scheme = APIKeyHeader(
    name="X-API-Key",
    scheme_name="ApiKeyAuth",
    auto_error=False,
)


def require_api_key(
    api_key: Annotated[str | None, Security(api_key_scheme)],
) -> str:
    if api_key is None:
        raise AppError(401, "MISSING_API_KEY", "Header X-API-Key wajib diisi.")

    group = verify_api_key(api_key)
    if group is None:
        raise AppError(401, "INVALID_API_KEY", "API key tidak valid.")
    return group
