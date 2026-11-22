from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..analysis.service import score_sessions
from ..config import settings
from ..errors import AppError
from ..identity.models import User
from ..tracking.models import SleepSession


def _sessions_by_user_for_date(
    db: Session,
    target_date: date,
    city: str | None,
) -> dict[str, tuple[User, list[SleepSession]]]:
    local_timezone = ZoneInfo(settings.timezone)
    start_utc = datetime.combine(
        target_date,
        time.min,
        tzinfo=local_timezone,
    ).astimezone(timezone.utc)
    end_utc = datetime.combine(
        target_date + timedelta(days=1),
        time.min,
        tzinfo=local_timezone,
    ).astimezone(timezone.utc)
    rows = db.execute(
        select(User, SleepSession)
        .join(SleepSession, SleepSession.user_id == User.id)
        .where(
            SleepSession.end_at >= start_utc,
            SleepSession.end_at < end_utc,
        )
    ).all()

    normalized_city = city.strip().casefold() if city is not None else None
    grouped: dict[str, tuple[User, list[SleepSession]]] = {}
    for user, session in rows:
        if normalized_city is not None:
            if user.city is None or user.city.strip().casefold() != normalized_city:
                continue
        if user.id not in grouped:
            grouped[user.id] = (user, [])
        grouped[user.id][1].append(session)
    return grouped


def _aggregate_scores(
    db: Session,
    target_date: date,
    city: str | None,
) -> tuple[float, int]:
    grouped = _sessions_by_user_for_date(db, target_date, city)
    user_averages: list[float] = []
    for user, sessions in grouped.values():
        scores = score_sessions(db, user, sessions)
        session_scores = [scores[session.id] for session in sessions if session.id in scores]
        if session_scores:
            user_averages.append(sum(session_scores) / len(session_scores))

    sample_size = len(user_averages)
    if sample_size < settings.aggregate_min_users:
        raise AppError(
            404,
            "NOT_ENOUGH_DATA",
            "Data agregat belum mencukupi.",
        )
    return round(sum(user_averages) / sample_size, 1), sample_size


def aggregate_city_score(
    db: Session,
    city: str,
    target_date: date,
) -> dict[str, object]:
    average_score, sample_size = _aggregate_scores(db, target_date, city)
    return {
        "city": city,
        "date": target_date,
        "average_score": average_score,
        "sample_size": sample_size,
    }


def aggregate_daily_score(
    db: Session,
    target_date: date,
) -> dict[str, object]:
    average_score, sample_size = _aggregate_scores(db, target_date, None)
    return {
        "date": target_date,
        "average_score": average_score,
        "sample_size": sample_size,
    }
