import logging
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, status: int, code: str, detail: Any) -> None:
        self.status = status
        self.code = code
        self.detail = detail
        super().__init__(str(detail))


def _response(
    status: int,
    code: str,
    detail: Any,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"code": code, "detail": detail},
        headers=headers,
    )


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return _response(exc.status, exc.code, exc.detail)


async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "TOO_MANY_REQUESTS",
    }
    return _response(
        exc.status_code,
        codes.get(exc.status_code, "HTTP_ERROR"),
        exc.detail,
        exc.headers,
    )


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    fields = []
    for error in exc.errors():
        location = error.get("loc", ())
        field = ".".join(
            str(part)
            for part in location
            if part not in {"body", "query", "path", "header", "cookie"}
        ) or "request"
        fields.append(
            {"field": field, "message": error.get("msg", "Nilai tidak valid.")}
        )
    return _response(
        422,
        "VALIDATION_ERROR",
        {"message": "Data yang dikirim tidak valid.", "fields": fields},
    )


async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error")
    return _response(500, "INTERNAL_ERROR", "Terjadi kesalahan internal.")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
