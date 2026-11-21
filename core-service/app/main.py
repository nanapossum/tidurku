from fastapi import FastAPI

from .config import settings

app = FastAPI(
    title="TidurKu",
    version="0.1.0",
    description="Layanan mikro pola tidur: skor, pola, rekomendasi, agregat anonim.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok", "service": settings.service_name}
