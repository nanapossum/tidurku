from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from ..config import settings
from .models import SleepSession


def _query_by_wake_date(
    db: Session,
    user_id: str,
    date_from: date | None,
    date_to: date | None,
) -> Select[tuple[SleepSession]]:
    query = select(SleepSession).where(SleepSession.user_id == user_id)
    local_timezone = ZoneInfo(settings.timezone)

    if date_from is not None:
        start_utc = datetime.combine(
            date_from,
            time.min,
            tzinfo=local_timezone,
        ).astimezone(timezone.utc)
        query = query.where(SleepSession.end_at >= start_utc)

    if date_to is not None:
        end_exclusive_utc = datetime.combine(
            date_to + timedelta(days=1),
            time.min,
            tzinfo=local_timezone,
        ).astimezone(timezone.utc)
        query = query.where(SleepSession.end_at < end_exclusive_utc)

    return query


def list_by_wake_date(
    db: Session,
    user_id: str,
    date_from: date | None,
    date_to: date | None,
    *,
    limit: int | None = None,
    offset: int = 0,
) -> list[SleepSession]:
    query = _query_by_wake_date(db, user_id, date_from, date_to).order_by(
        SleepSession.start_at.desc(),
        SleepSession.id.desc(),
    )
    if limit is not None:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    return list(db.scalars(query).all())


def count_by_wake_date(
    db: Session,
    user_id: str,
    date_from: date | None,
    date_to: date | None,
) -> int:
    query = _query_by_wake_date(db, user_id, date_from, date_to)
    return db.scalar(select(func.count()).select_from(query.subquery())) or 0


def has_overlap(
    db: Session,
    user_id: str,
    start_at: datetime,
    end_at: datetime,
    exclude_id: str | None = None,
) -> bool:
    query = select(SleepSession.id).where(
        SleepSession.user_id == user_id,
        SleepSession.start_at < end_at,
        SleepSession.end_at > start_at,
    )
    if exclude_id is not None:
        query = query.where(SleepSession.id != exclude_id)
    return db.scalar(query.limit(1)) is not None


def get(db: Session, user_id: str, id: str) -> SleepSession | None:
    return db.scalar(
        select(SleepSession).where(
            SleepSession.id == id,
            SleepSession.user_id == user_id,
        )
    )
