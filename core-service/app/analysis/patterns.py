from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Literal

from .records import SleepRecord
from .rules import (
    LATE_NIGHT_END_MINUTE,
    LATE_NIGHT_MIN_DAYS,
    LATE_NIGHT_START_MINUTE,
    LATE_NIGHT_WINDOW_DAYS,
    MIN_SESSIONS_FOR_PATTERNS,
    R02_INCONSISTENCY_MINUTES,
    R03_CONSECUTIVE_SHORT_DAYS,
    R03_SHORT_SLEEP_MINUTES,
    R04_SLEEP_DEBT_WINDOW_DAYS,
)
from .scoring import (
    baseline_bedtime_minutes,
    circular_difference_minutes,
    minutes_of_day,
)


@dataclass(frozen=True)
class Pattern:
    type: Literal["inconsistent_schedule", "late_night_repeat", "sleep_debt"]
    severity: Literal["info", "warning"]
    message: str


@dataclass(frozen=True)
class PatternAnalysis:
    patterns_available: bool
    patterns: tuple[Pattern, ...]
    sleep_debt_minutes: int
    debt_warning: bool


def _daily_durations(records: tuple[SleepRecord, ...]) -> dict[date, float]:
    durations: dict[date, float] = {}
    for record in records:
        wake_date = record.end_local.date()
        durations[wake_date] = durations.get(wake_date, 0.0) + record.duration_min
    return durations


def analyze_patterns(
    records: Iterable[SleepRecord],
    target_hours: float,
    session_count: int | None = None,
    as_of_date: date | None = None,
) -> PatternAnalysis:
    records = tuple(records)
    available_count = len(records) if session_count is None else session_count
    if not records:
        return PatternAnalysis(False, (), 0, False)

    last_data_date = max(record.end_local.date() for record in records)
    window_end_date = as_of_date or last_data_date
    first_window_date = window_end_date - timedelta(
        days=R04_SLEEP_DEBT_WINDOW_DAYS - 1
    )
    durations_by_wake_date = _daily_durations(records)
    target_minutes = target_hours * 60
    debt_minutes = round(
        sum(
            max(0.0, target_minutes - duration)
            for wake_date, duration in durations_by_wake_date.items()
            if first_window_date <= wake_date <= window_end_date
        )
    )

    consecutive_short_days = 0
    for day_offset in range(R03_CONSECUTIVE_SHORT_DAYS):
        wake_date = last_data_date - timedelta(days=day_offset)
        daily_duration = durations_by_wake_date.get(wake_date)
        if daily_duration is None or daily_duration >= R03_SHORT_SLEEP_MINUTES:
            break
        consecutive_short_days += 1
    debt_warning = consecutive_short_days >= R03_CONSECUTIVE_SHORT_DAYS

    patterns_available = available_count >= MIN_SESSIONS_FOR_PATTERNS
    if not patterns_available:
        return PatternAnalysis(False, (), debt_minutes, debt_warning)

    patterns: list[Pattern] = []
    latest = max(records, key=lambda record: record.end_local)
    baseline = baseline_bedtime_minutes(latest, records)
    if baseline is not None:
        deviation = circular_difference_minutes(
            minutes_of_day(latest.start_local),
            baseline,
        )
        if deviation > R02_INCONSISTENCY_MINUTES:
            patterns.append(
                Pattern(
                    "inconsistent_schedule",
                    "warning",
                    "Jam tidur terbaru menyimpang lebih dari 90 menit dari baseline.",
                )
            )

    late_window_start = window_end_date - timedelta(
        days=LATE_NIGHT_WINDOW_DAYS - 1
    )
    late_bedtime_dates = {
        record.start_local.date()
        for record in records
        if late_window_start <= record.start_local.date() <= window_end_date
        and LATE_NIGHT_START_MINUTE
        <= minutes_of_day(record.start_local)
        < LATE_NIGHT_END_MINUTE
    }
    if len(late_bedtime_dates) >= LATE_NIGHT_MIN_DAYS:
        patterns.append(
            Pattern(
                "late_night_repeat",
                "info",
                "Jam tidur berada pada rentang 00:00–04:59 setidaknya 3 hari.",
            )
        )

    if debt_warning:
        patterns.append(
            Pattern(
                "sleep_debt",
                "warning",
                "Durasi tidur kurang dari 6 jam selama 3 hari berturut-turut.",
            )
        )

    return PatternAnalysis(
        patterns_available,
        tuple(patterns),
        debt_minutes,
        debt_warning,
    )
