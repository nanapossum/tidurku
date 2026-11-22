from datetime import date

from sqlalchemy.orm import Session

from ..errors import AppError
from ..events import SleepSessionRecorded, publish
from ..identity.models import User
from . import repository
from .models import SleepSession
from .schemas import SleepSessionIn


MAX_SESSION_SECONDS = 16 * 60 * 60


def _validate_time_range(data: SleepSessionIn) -> None:
    duration_seconds = (data.end_at - data.start_at).total_seconds()
    if duration_seconds <= 0:
        raise AppError(
            422,
            "INVALID_TIME_RANGE",
            "Waktu bangun harus setelah waktu tidur.",
        )
    if duration_seconds > MAX_SESSION_SECONDS:
        raise AppError(
            422,
            "DURATION_TOO_LONG",
            "Durasi sesi tidur tidak boleh lebih dari 16 jam.",
        )


def _ensure_no_overlap(
    db: Session,
    user_id: str,
    data: SleepSessionIn,
    exclude_id: str | None = None,
) -> None:
    if repository.has_overlap(
        db,
        user_id,
        data.start_at,
        data.end_at,
        exclude_id,
    ):
        raise AppError(
            409,
            "SESSION_OVERLAP",
            "Waktu sesi bertumpang tindih dengan sesi tidur lain.",
        )


def create_session(
    db: Session,
    user: User,
    data: SleepSessionIn,
) -> SleepSession:
    _validate_time_range(data)
    _ensure_no_overlap(db, user.id, data)
    session = SleepSession(
        user_id=user.id,
        start_at=data.start_at,
        end_at=data.end_at,
        quality=data.quality,
        stress=data.stress,
        caffeine=data.caffeine,
        screen_minutes=data.screen_minutes,
        notes=data.notes,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    publish(SleepSessionRecorded(user.id, session.id, "create"), db)
    return session


def list_sessions(
    db: Session,
    user: User,
    date_from: date | None,
    date_to: date | None,
    limit: int,
    offset: int,
) -> tuple[list[SleepSession], int]:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise AppError(422, "INVALID_DATE_RANGE", "Rentang tanggal tidak valid.")
    total = repository.count_by_wake_date(db, user.id, date_from, date_to)
    items = repository.list_by_wake_date(
        db,
        user.id,
        date_from,
        date_to,
        limit=limit,
        offset=offset,
    )
    return items, total


def get_session(db: Session, user: User, session_id: str) -> SleepSession:
    session = repository.get(db, user.id, session_id)
    if session is None:
        raise AppError(404, "NOT_FOUND", "Sesi tidur tidak ditemukan.")
    return session


def update_session(
    db: Session,
    user: User,
    session_id: str,
    data: SleepSessionIn,
) -> SleepSession:
    session = get_session(db, user, session_id)
    _validate_time_range(data)
    _ensure_no_overlap(db, user.id, data, exclude_id=session.id)
    session.start_at = data.start_at
    session.end_at = data.end_at
    session.quality = data.quality
    session.stress = data.stress
    session.caffeine = data.caffeine
    session.screen_minutes = data.screen_minutes
    session.notes = data.notes
    db.commit()
    db.refresh(session)
    publish(SleepSessionRecorded(user.id, session.id, "update"), db)
    return session


def delete_session(db: Session, user: User, session_id: str) -> None:
    session = get_session(db, user, session_id)
    deleted_id = session.id
    db.delete(session)
    db.commit()
    publish(SleepSessionRecorded(user.id, deleted_id, "delete"), db)
