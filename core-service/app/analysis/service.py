from datetime import date, datetime, timedelta
from typing import Protocol, Sequence
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from ..config import settings
from ..goals.service import get_goal
from ..identity.models import User
from ..tracking import repository
from .patterns import analyze_patterns
from .records import SleepRecord
from .rules import MIN_SESSIONS_FOR_PATTERNS
from .scoring import score_records
from .summary import WeeklySummary, build_weekly_summary


class SessionRecordSource(Protocol):
    id: str
    start_at: datetime
    end_at: datetime
    quality: int | None


def _to_record(session: SessionRecordSource, local_timezone: ZoneInfo) -> SleepRecord:
    start_local = session.start_at.astimezone(local_timezone)
    end_local = session.end_at.astimezone(local_timezone)
    duration_min = (session.end_at - session.start_at).total_seconds() / 60
    return SleepRecord(
        id=session.id,
        start_local=start_local,
        end_local=end_local,
        duration_min=duration_min,
        quality=session.quality,
    )


def _records_between(
    db: Session,
    user: User,
    date_from: date,
    date_to: date,
) -> list[SleepRecord]:
    local_timezone = ZoneInfo(settings.timezone)
    sessions = repository.list_by_wake_date(
        db,
        user.id,
        date_from,
        date_to,
    )
    return [_to_record(session, local_timezone) for session in sessions]


def score_sessions(
    db: Session,
    user: User,
    sessions: Sequence[SessionRecordSource],
) -> dict[str, int]:
    if not sessions:
        return {}
    local_timezone = ZoneInfo(settings.timezone)
    local_wake_dates = [
        session.end_at.astimezone(local_timezone).date() for session in sessions
    ]
    date_from = min(local_wake_dates) - timedelta(days=7)
    date_to = max(local_wake_dates)
    records = _records_between(db, user, date_from, date_to)
    results = score_records(records)
    return {
        session.id: results[session.id].score
        for session in sessions
        if session.id in results
    }


def get_sleep_score(db: Session, user: User) -> dict[str, object]:
    latest_sessions = repository.list_by_wake_date(
        db,
        user.id,
        None,
        None,
        limit=1,
    )
    session_count = repository.count_by_wake_date(db, user.id, None, None)
    if not latest_sessions:
        return {
            "latest": None,
            "weekly_average": None,
            "session_count": session_count,
        }

    local_timezone = ZoneInfo(settings.timezone)
    latest_session = latest_sessions[0]
    latest_record = _to_record(latest_session, local_timezone)
    latest_wake_date = latest_record.end_local.date()
    today = datetime.now(local_timezone).date()
    baseline_records = _records_between(
        db,
        user,
        latest_wake_date - timedelta(days=7),
        latest_wake_date,
    )
    weekly_records = _records_between(
        db,
        user,
        today - timedelta(days=13),
        today,
    )
    records_by_id = {record.id: record for record in baseline_records}
    records_by_id.update({record.id: record for record in weekly_records})
    records = list(records_by_id.values())
    results = score_records(records)
    latest_result = results[latest_record.id]
    current_week_records = [
        record
        for record in records
        if today - timedelta(days=6) <= record.end_local.date() <= today
    ]
    weekly_scores = [results[record.id].score for record in current_week_records]

    return {
        "latest": {
            "session_id": latest_record.id,
            "score": latest_result.score,
            "breakdown": latest_result,
            "deviation_minutes": latest_result.deviation_minutes,
        },
        "weekly_average": (
            sum(weekly_scores) / len(weekly_scores) if weekly_scores else None
        ),
        "session_count": session_count,
    }


def get_patterns(db: Session, user: User) -> dict[str, object]:
    latest_sessions = repository.list_by_wake_date(
        db,
        user.id,
        None,
        None,
        limit=1,
    )
    session_count = repository.count_by_wake_date(db, user.id, None, None)
    if not latest_sessions:
        result = analyze_patterns((), get_goal(db, user).target_hours, session_count)
    else:
        local_timezone = ZoneInfo(settings.timezone)
        latest_record = _to_record(latest_sessions[0], local_timezone)
        latest_wake_date = latest_record.end_local.date()
        today = datetime.now(local_timezone).date()
        baseline_records = _records_between(
            db,
            user,
            latest_wake_date - timedelta(days=7),
            latest_wake_date,
        )
        recent_records = _records_between(
            db,
            user,
            today - timedelta(days=6),
            today,
        )
        records_by_id = {record.id: record for record in baseline_records}
        records_by_id.update({record.id: record for record in recent_records})
        records = list(records_by_id.values())
        target_hours = get_goal(db, user).target_hours
        result = analyze_patterns(records, target_hours, session_count, today)
    return {
        "patterns_available": result.patterns_available,
        "min_sessions": MIN_SESSIONS_FOR_PATTERNS,
        "patterns": result.patterns,
        "sleep_debt_minutes": result.sleep_debt_minutes,
        "debt_warning": result.debt_warning,
    }


def get_weekly_summary(
    db: Session,
    user: User,
    week_start: date | None = None,
) -> WeeklySummary:
    local_timezone = ZoneInfo(settings.timezone)
    if week_start is None:
        today = datetime.now(local_timezone).date()
        week_start = today - timedelta(days=today.weekday())

    records = _records_between(
        db,
        user,
        week_start - timedelta(days=7),
        week_start + timedelta(days=6),
    )
    target_hours = get_goal(db, user).target_hours
    return build_weekly_summary(records, week_start, target_hours)
