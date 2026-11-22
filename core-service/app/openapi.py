from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    detail: Any


ERROR_RESPONSES = {
    401: {
        "model": ErrorResponse,
        "description": "Autentikasi atau API key tidak valid.",
        "content": {
            "application/json": {
                "example": {
                    "code": "NOT_AUTHENTICATED",
                    "detail": "Autentikasi diperlukan.",
                }
            }
        },
    },
    404: {
        "model": ErrorResponse,
        "description": "Sumber daya tidak ditemukan atau data belum mencukupi.",
        "content": {
            "application/json": {
                "example": {
                    "code": "NOT_FOUND",
                    "detail": "Sumber daya tidak ditemukan.",
                }
            }
        },
    },
    409: {
        "model": ErrorResponse,
        "description": "Konflik dengan data yang sudah ada.",
        "content": {
            "application/json": {
                "example": {
                    "code": "CONFLICT",
                    "detail": "Data bertentangan dengan sumber daya yang ada.",
                }
            }
        },
    },
    422: {
        "model": ErrorResponse,
        "description": "Data permintaan tidak valid.",
        "content": {
            "application/json": {
                "example": {
                    "code": "VALIDATION_ERROR",
                    "detail": {
                        "message": "Data yang dikirim tidak valid.",
                        "fields": [
                            {"field": "field", "message": "Nilai tidak valid."}
                        ],
                    },
                }
            }
        },
    },
}
