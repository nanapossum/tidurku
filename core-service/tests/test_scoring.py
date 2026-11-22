from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.analysis.records import SleepRecord
from app.analysis.scoring import (
    baseline_bedtime_minutes,
    circular_difference_minutes,
    circular_mean_minutes,
    score_record,
)


LOCAL = ZoneInfo("Asia/Jakarta")


def make_record(
    record_id,
    wake_date,
    bedtime_hour=22,
    bedtime_minute=0,
    duration_min=480,
    quality=None,
):
    start_date = wake_date - timedelta(days=1) if bedtime_hour >= 12 else wake_date
    start = datetime(
        start_date.year,
        start_date.month,
        start_date.day,
        bedtime_hour,
        tzinfo=LOCAL,
    ) + timedelta(minutes=bedtime_minute)
    end = start + timedelta(minutes=duration_min)
    return SleepRecord(record_id, start, end, duration_min, quality)


@pytest.mark.parametrize(
    ("duration_min", "expected_duration_score"),
    [
        (6 * 60 + 59, 100 - 20 / 60),
        (7 * 60, 100),
        (9 * 60, 100),
        (9 * 60 + 1, 100 - 20 / 60),
    ],
)
def test_duration_score_boundaries(duration_min, expected_duration_score):
    record = make_record("session", datetime(2026, 1, 1).date(), duration_min=duration_min)
    result = score_record(record, [record])
    assert result.duration_score == pytest.approx(expected_duration_score)
    assert result.consistency_score is None
    assert result.quality_score is None
    assert result.score == round(expected_duration_score)


@pytest.mark.parametrize(
    ("deviation", "expected_score"),
    [
        (30, 100),
        (31, 100 - 50 / 60),
        (90, 50),
        (91, 25 - 25 / 90),
    ],
)
def test_consistency_score_boundaries(deviation, expected_score):
    previous = [
        make_record(
            f"prior-{day}",
            datetime(2026, 1, day).date(),
        )
        for day in (1, 2, 3)
    ]
    latest = make_record(
        "latest",
        datetime(2026, 1, 4).date(),
        bedtime_minute=deviation,
    )
    result = score_record(latest, [*previous, latest])
    assert result.deviation_minutes == pytest.approx(deviation)
    assert result.consistency_score == pytest.approx(expected_score)


def test_circular_mean_and_difference_cross_midnight():
    mean = circular_mean_minutes([23 * 60 + 30, 0, 30])
    assert mean is not None
    assert circular_difference_minutes(mean, 0) < 1e-8
    assert circular_difference_minutes(23 * 60 + 59, 11 * 60 + 59) == 720


def test_baseline_requires_three_other_sessions_in_previous_seven_wake_dates():
    target = make_record("target", datetime(2026, 1, 10).date())
    two_recent = [
        make_record(f"recent-{day}", datetime(2026, 1, day).date())
        for day in (8, 9)
    ]
    old = make_record("old", datetime(2026, 1, 2).date())
    same_wake_date = make_record("same-day", datetime(2026, 1, 10).date())

    assert baseline_bedtime_minutes(target, [*two_recent, old, target]) is None
    third_recent = make_record("recent-7", datetime(2026, 1, 7).date())
    baseline = baseline_bedtime_minutes(
        target,
        [*two_recent, third_recent, old, same_wake_date, target],
    )
    assert baseline == pytest.approx(22 * 60)


def test_score_renormalizes_weights_for_missing_components():
    no_components = make_record("duration-only", datetime(2026, 1, 1).date())
    assert score_record(no_components, [no_components]).score == 100

    quality_only = make_record(
        "duration-quality",
        datetime(2026, 1, 1).date(),
        duration_min=7 * 60,
        quality=1,
    )
    result = score_record(quality_only, [quality_only])
    assert result.duration_score == 100
    assert result.quality_score == 0
    assert result.score == 62

    complete = make_record(
        "complete",
        datetime(2026, 1, 4).date(),
        quality=1,
    )
    baseline_records = [
        make_record(f"baseline-{day}", datetime(2026, 1, day).date())
        for day in (1, 2, 3)
    ]
    result = score_record(complete, [*baseline_records, complete])
    assert result.consistency_score == 100
    assert result.quality_score == 0
    assert result.score == 75
