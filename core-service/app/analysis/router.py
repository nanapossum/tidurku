from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..identity.deps import get_current_user
from ..identity.models import User
from ..openapi import ERROR_RESPONSES
from .schemas import PatternsOut, SleepScoreOut, WeeklySummaryOut
from .service import get_patterns, get_sleep_score, get_weekly_summary


router = APIRouter(tags=["Analysis"], responses=ERROR_RESPONSES)


@router.get(
    "/api/sleep-score",
    response_model=SleepScoreOut,
    summary="Lihat skor tidur",
    description="Mengembalikan skor sesi terbaru, rincian skor, dan rata-rata mingguan.",
)
def read_sleep_score(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SleepScoreOut:
    return get_sleep_score(db, current_user)


@router.get(
    "/api/patterns",
    response_model=PatternsOut,
    summary="Lihat pola tidur",
    description="Menganalisis pola tidur, utang tidur, dan peringatannya.",
)
def read_patterns(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PatternsOut:
    return get_patterns(db, current_user)


@router.get(
    "/api/summary/weekly",
    response_model=WeeklySummaryOut,
    summary="Ringkasan mingguan",
    description="Merangkum durasi, skor, dan target tidur untuk satu pekan lokal.",
)
def read_weekly_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    week_start: Annotated[date | None, Query(alias="weekStart")] = None,
) -> WeeklySummaryOut:
    return get_weekly_summary(db, current_user, week_start)
