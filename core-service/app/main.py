
from fastapi import FastAPI, HTTPException

from .config import settings
from .database import check_database_connection


app = FastAPI(
    title="TidurKu",
    version="0.1.0",
    description="Layanan mikro pola tidur: skor, pola, rekomendasi, agregat anonim.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


@app.get("/api/health", tags=["system"])
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
