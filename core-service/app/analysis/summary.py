from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable

from .records import SleepRecord
from .scoring import score_records


@dataclass(frozen=True)
class SummaryDay:
    date: date
    session_count: int
    duration_minutes: int | None
    score: int | None
    met_goal: bool | None


@dataclass(frozen=True)
class WeeklySummary:
    week_start: date
    days: tuple[SummaryDay, ...]
    average_duration_minutes: float | None
    average_score: float | None
    days_meeting_goal: int


def build_weekly_summary(
    records: Iterable[SleepRecord],
    week_start: date,
    target_hours: float,
) -> WeeklySummary:
    records = tuple(records)
    week_end = week_start + timedelta(days=6)
    records_by_wake_date: dict[date, list[SleepRecord]] = {}
    for record in records:
        wake_date = record.end_local.date()
        if week_start <= wake_date <= week_end:
            records_by_wake_date.setdefault(wake_date, []).append(record)

    scores = score_records(records)
    days: list[SummaryDay] = []
    session_scores: list[int] = []
    recorded_daily_durations: list[int] = []
    days_meeting_goal = 0
    for day_offset in range(7):
        current_date = week_start + timedelta(days=day_offset)
        daily_records = records_by_wake_date.get(current_date, [])
        if not daily_records:
            days.append(SummaryDay(current_date, 0, None, None, None))
            continue

        total_duration = sum(record.duration_min for record in daily_records)
        duration_minutes = round(total_duration)
        daily_scores = [scores[record.id].score for record in daily_records]
        daily_score = round(sum(daily_scores) / len(daily_scores))
        met_goal = total_duration >= target_hours * 60
        days_meeting_goal += int(met_goal)
        session_scores.extend(daily_scores)
        recorded_daily_durations.append(duration_minutes)
        days.append(
            SummaryDay(
                current_date,
                len(daily_records),
                duration_minutes,
                daily_score,
                met_goal,
            )
        )

    return WeeklySummary(
        week_start=week_start,
        days=tuple(days),
        average_duration_minutes=(
            sum(recorded_daily_durations) / len(recorded_daily_durations)
            if recorded_daily_durations
            else None
        ),
        average_score=(
            sum(session_scores) / len(session_scores) if session_scores else None
        ),
        days_meeting_goal=days_meeting_goal,
    )
