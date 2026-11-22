
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException

from .config import settings
from .database import check_database_connection, init_db
from .errors import register_exception_handlers
from .analysis.router import router as analysis_router
from .environment.router import router as environment_router
from .goals.router import router as goals_router
from .goals.router import recommendations_router
from .identity.router import router as identity_router
from .public.router import router as public_router
from .reminders.router import router as reminders_router
from .tracking.router import router as tracking_router


OPENAPI_TAGS = [
    {"name": "Identity", "description": "Registrasi, autentikasi, dan profil pengguna."},
    {"name": "Tracking", "description": "Pencatatan dan pengelolaan sesi tidur."},
    {"name": "Goals", "description": "Target tidur dan rekomendasi personal."},
    {"name": "Analysis", "description": "Skor, pola, dan ringkasan tidur."},
    {"name": "Reminders", "description": "Pengaturan waktu pengingat tidur."},
    {"name": "Environment", "description": "Korelasi faktor lingkungan dengan skor tidur."},
    {"name": "Public", "description": "Agregat anonim yang dilindungi API key."},
    {"name": "System", "description": "Status kesehatan layanan."},
]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    from . import models_registry
    from .reminders.handlers import register_handlers

    _ = models_registry
    register_handlers()
    init_db()
    yield


app = FastAPI(
    title="TidurKu",
    version="0.1.0",
    description="Layanan mikro pola tidur: skor, pola, rekomendasi, agregat anonim.",
    openapi_tags=OPENAPI_TAGS,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
register_exception_handlers(app)
app.include_router(identity_router)
app.include_router(tracking_router)
app.include_router(goals_router)
app.include_router(recommendations_router)
app.include_router(reminders_router)
app.include_router(analysis_router)
app.include_router(environment_router)
app.include_router(public_router)


@app.get(
    "/api/health",
    tags=["System"],
    summary="Periksa kesehatan layanan",
    description="Memeriksa layanan dan koneksi database.",
    responses={
        200: {
            "description": "Layanan dan database berfungsi.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "tidurku",
                        "database": "connected",
                    }
                }
            },
        },
        503: {
            "description": "Database tidak tersedia.",
            "content": {
                "application/json": {
                    "example": {
                        "code": "HTTP_ERROR",
                        "detail": {
                            "status": "unhealthy",
                            "service": "tidurku",
                            "database": "disconnected",
                        }
                    }
                }
            },
        },
    },
)
def health():
    database_connected = check_database_connection()

    if not database_connected:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "service": settings.service_name,
                "database": "disconnected",
            },
        )

    return {
        "status": "healthy",
        "service": settings.service_name,
        "database": "connected",
    }
