import logging
from datetime import date, datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..openapi import ERROR_RESPONSES
from .deps import require_api_key
from .schemas import CityScoreAggregateOut, DailyScoreAggregateOut
from .service import aggregate_city_score, aggregate_daily_score


logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/public/aggregate",
    tags=["Public"],
    responses=ERROR_RESPONSES,
)


def _default_date() -> date:
    today = datetime.now(ZoneInfo(settings.timezone)).date()
    return today - timedelta(days=1)


@router.get(
    "/score",
    response_model=CityScoreAggregateOut,
    summary="Agregat skor kota",
    description=(
        "Menghitung rata-rata skor antarpengguna pada suatu kota dan tanggal. "
        "Hasil hanya tersedia jika ambang anonimitas terpenuhi."
    ),
)
def city_score_aggregate(
    api_key_group: Annotated[str, Depends(require_api_key)],
    db: Annotated[Session, Depends(get_db)],
    city: Annotated[
        str,
        Query(
            min_length=1,
            max_length=60,
            description="Nama kota untuk pemfilteran tanpa membedakan kapitalisasi.",
            examples=["Bandung"],
        ),
    ],
    target_date: Annotated[
        date | None,
        Query(alias="date", description="Tanggal bangun lokal.", examples=["2026-11-21"]),
    ] = None,
) -> dict[str, object]:
    logger.info(
        "Public aggregate requested by API key group %s",
        api_key_group,
        extra={"aggregate_type": "city_score"},
    )
    return aggregate_city_score(db, city, target_date or _default_date())


@router.get(
    "/daily",
    response_model=DailyScoreAggregateOut,
    summary="Agregat skor harian",
    description=(
        "Menghitung rata-rata skor antarpengguna untuk semua kota pada tanggal tertentu."
    ),
)
def daily_score_aggregate(
    api_key_group: Annotated[str, Depends(require_api_key)],
    db: Annotated[Session, Depends(get_db)],
    target_date: Annotated[
        date | None,
        Query(alias="date", description="Tanggal bangun lokal.", examples=["2026-11-21"]),
    ] = None,
) -> dict[str, object]:
    logger.info(
        "Public aggregate requested by API key group %s",
        api_key_group,
        extra={"aggregate_type": "daily"},
    )
    return aggregate_daily_score(db, target_date or _default_date())
