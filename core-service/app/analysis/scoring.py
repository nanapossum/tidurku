import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from .records import SleepRecord
from .rules import (
    BASELINE_WINDOW_DAYS,
    CONSISTENCY_FULL_SCORE_MINUTES,
    CONSISTENCY_SCORE_AFTER_INCONSISTENCY_LIMIT,
    CONSISTENCY_SCORE_AT_INCONSISTENCY_LIMIT,
    CONSISTENCY_SCORE_WEIGHT,
    DURATION_SCORE_PENALTY_PER_HOUR,
    DURATION_SCORE_WEIGHT,
    MAX_CIRCULAR_DEVIATION_MINUTES,
    QUALITY_SCORE_WEIGHT,
    R01_MAX_SLEEP_HOURS,
    R01_MIN_SLEEP_HOURS,
    R02_INCONSISTENCY_MINUTES,
)


MINUTES_PER_DAY = 24 * 60


@dataclass(frozen=True)
class ScoreResult:
    score: int
    duration_score: float
    consistency_score: float | None
    quality_score: float | None
    deviation_minutes: float | None


def minutes_of_day(value: datetime) -> float:
    return (
        value.hour * 60
        + value.minute
        + value.second / 60
        + value.microsecond / 60_000_000
    )


def circular_mean_minutes(values: Iterable[float]) -> float | None:
    minutes = [value % MINUTES_PER_DAY for value in values]
    if not minutes:
        return None

    angles = [2 * math.pi * value / MINUTES_PER_DAY for value in minutes]
    sin_mean = sum(math.sin(angle) for angle in angles)
    cos_mean = sum(math.cos(angle) for angle in angles)
    if math.isclose(sin_mean, 0, abs_tol=1e-12) and math.isclose(
        cos_mean, 0, abs_tol=1e-12
    ):
        return minutes[0]

    angle = math.atan2(sin_mean, cos_mean) % (2 * math.pi)
    result = (angle * MINUTES_PER_DAY / (2 * math.pi)) % MINUTES_PER_DAY
    return 0.0 if math.isclose(result, MINUTES_PER_DAY, abs_tol=1e-9) else result


def circular_difference_minutes(first: float, second: float) -> float:
    difference = (
        (first - second + MAX_CIRCULAR_DEVIATION_MINUTES)
        % MINUTES_PER_DAY
        - MAX_CIRCULAR_DEVIATION_MINUTES
    )
    return round(abs(difference), 10)


def baseline_bedtime_minutes(
    record: SleepRecord,
    records: Iterable[SleepRecord],
) -> float | None:
    wake_date = record.end_local.date()
    earliest_date = wake_date - timedelta(days=BASELINE_WINDOW_DAYS)
    previous_bedtimes = [
        minutes_of_day(candidate.start_local)
        for candidate in records
        if candidate.id != record.id
        and earliest_date <= candidate.end_local.date() < wake_date
    ]
    if len(previous_bedtimes) < 3:
        return None
    return circular_mean_minutes(previous_bedtimes)


def _duration_score(duration_min: float) -> float:
    duration_hours = duration_min / 60
    if R01_MIN_SLEEP_HOURS <= duration_hours <= R01_MAX_SLEEP_HOURS:
        return 100.0
    hours_outside_range = (
        R01_MIN_SLEEP_HOURS - duration_hours
        if duration_hours < R01_MIN_SLEEP_HOURS
        else duration_hours - R01_MAX_SLEEP_HOURS
    )
    return max(
        0.0,
        100.0 - DURATION_SCORE_PENALTY_PER_HOUR * hours_outside_range,
    )


def _consistency_score(deviation_minutes: float) -> float:
    if deviation_minutes <= CONSISTENCY_FULL_SCORE_MINUTES:
        return 100.0
    if deviation_minutes <= R02_INCONSISTENCY_MINUTES:
        span = R02_INCONSISTENCY_MINUTES - CONSISTENCY_FULL_SCORE_MINUTES
        score_range = 100.0 - CONSISTENCY_SCORE_AT_INCONSISTENCY_LIMIT
        return (
            100.0
            - (deviation_minutes - CONSISTENCY_FULL_SCORE_MINUTES)
            * (score_range / span)
        )
    return max(
        0.0,
        CONSISTENCY_SCORE_AFTER_INCONSISTENCY_LIMIT
        - (deviation_minutes - R02_INCONSISTENCY_MINUTES)
        * (CONSISTENCY_SCORE_AFTER_INCONSISTENCY_LIMIT / R02_INCONSISTENCY_MINUTES),
    )


def score_record(
    record: SleepRecord,
    records: Iterable[SleepRecord],
) -> ScoreResult:
    all_records = tuple(records)
    duration_score = _duration_score(record.duration_min)
    baseline = baseline_bedtime_minutes(record, all_records)
    if baseline is None:
        deviation_minutes = None
        consistency_score = None
    else:
        deviation_minutes = circular_difference_minutes(
            minutes_of_day(record.start_local),
            baseline,
        )
        consistency_score = _consistency_score(deviation_minutes)

    quality_score = (
        None
        if record.quality is None
        else (record.quality - 1) / 4 * 100
    )
    weighted_scores = [(duration_score, DURATION_SCORE_WEIGHT)]
    if consistency_score is not None:
        weighted_scores.append((consistency_score, CONSISTENCY_SCORE_WEIGHT))
    if quality_score is not None:
        weighted_scores.append((quality_score, QUALITY_SCORE_WEIGHT))
    normalized_score = sum(
        score * weight for score, weight in weighted_scores
    ) / sum(weight for _, weight in weighted_scores)

    return ScoreResult(
        score=int(round(normalized_score)),
        duration_score=duration_score,
        consistency_score=consistency_score,
        quality_score=quality_score,
        deviation_minutes=deviation_minutes,
    )


def score_records(records: Iterable[SleepRecord]) -> dict[str, ScoreResult]:
    all_records = tuple(records)
    return {
        record.id: score_record(record, all_records)
        for record in all_records
    }
