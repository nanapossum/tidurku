from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..errors import AppError
from ..identity.deps import get_current_user
from ..identity.models import User
from ..openapi import ERROR_RESPONSES
from .models import RecommendationCompletion
from .recommendations import RECOMMENDATION_CODES, build_recommendations
from .schemas import GoalOut, GoalUpdateIn
from .service import get_goal, update_goal


router = APIRouter(
    prefix="/api/goal",
    tags=["Goals"],
    responses=ERROR_RESPONSES,
)
recommendations_router = APIRouter(
    prefix="/api/recommendations",
    tags=["Goals"],
    responses=ERROR_RESPONSES,
)


@router.get(
    "",
    response_model=GoalOut,
    summary="Lihat target tidur",
    description="Mengembalikan target tidur dan rentang sehat berdasarkan usia.",
)
def read_goal(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GoalOut:
    return get_goal(db, current_user)


@router.put(
    "",
    response_model=GoalOut,
    summary="Perbarui target tidur",
    description="Menyimpan target jam tidur dan waktu tidur pengguna.",
)
def put_goal(
    data: GoalUpdateIn,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GoalOut:
    return update_goal(db, current_user, data)


@recommendations_router.get(
    "",
    summary="Lihat rekomendasi",
    description="Menghasilkan rekomendasi berdasarkan pola tidur pengguna.",
    responses={
        200: {
            "description": "Rekomendasi yang tersedia untuk hari ini.",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": "shift_bedtime_earlier",
                                "text": "Geser jam tidur 30 menit lebih awal.",
                                "shiftMinutes": -30,
                                "basedOn": "late_night_repeat",
                                "done": False,
                            }
                        ],
                        "basedOnPatterns": ["late_night_repeat"],
                    }
                }
            },
        }
    },
)
def read_recommendations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    from ..analysis.service import get_patterns

    pattern_data = get_patterns(db, current_user)
    recommendations = build_recommendations(pattern_data, get_goal(db, current_user))
    today = datetime.now(ZoneInfo(settings.timezone)).date()
    completed = set(
        db.scalars(
            select(RecommendationCompletion.code).where(
                RecommendationCompletion.user_id == current_user.id,
                RecommendationCompletion.date_local == today,
            )
        ).all()
    )
    items = [
        {**item, "done": item["id"] in completed}
        for item in recommendations
    ]
    based_on_patterns = (
        [pattern.type for pattern in pattern_data["patterns"]]
        if pattern_data["patterns_available"]
        else []
    )
    return {"items": items, "basedOnPatterns": based_on_patterns}


@recommendations_router.post(
    "/{recommendation_id}/complete",
    summary="Tandai rekomendasi selesai",
    description="Mencatat penyelesaian rekomendasi untuk tanggal lokal hari ini.",
    responses={
        200: {
            "description": "Status rekomendasi setelah ditandai selesai.",
            "content": {
                "application/json": {
                    "example": {"id": "track_sleep_3_nights", "done": True}
                }
            },
        }
    },
)
def complete_recommendation(
    recommendation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    if recommendation_id not in RECOMMENDATION_CODES:
        raise AppError(
            404,
            "RECOMMENDATION_NOT_FOUND",
            "Rekomendasi tidak ditemukan.",
        )

    today = datetime.now(ZoneInfo(settings.timezone)).date()
    completion_id = (current_user.id, recommendation_id, today)
    if db.get(RecommendationCompletion, completion_id) is None:
        db.add(
            RecommendationCompletion(
                user_id=current_user.id,
                code=recommendation_id,
                date_local=today,
            )
        )
        db.commit()
    return {"id": recommendation_id, "done": True}
