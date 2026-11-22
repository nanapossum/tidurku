from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.analysis.records import SleepRecord
from app.analysis.summary import build_weekly_summary


LOCAL = ZoneInfo("Asia/Jakarta")


def record(record_id, wake_date, duration_min, quality=None):
    start = datetime.combine(
        wake_date - timedelta(days=1),
        datetime.min.time().replace(hour=22),
        tzinfo=LOCAL,
    )
    end = start + timedelta(minutes=duration_min)
    return SleepRecord(record_id, start, end, duration_min, quality)


def test_weekly_summary_includes_empty_days_and_daily_aggregates():
    week_start = date(2026, 11, 16)
    baseline = [
        record(f"baseline-{day}", date(2026, 11, day), 8 * 60, 4)
        for day in (9, 10, 11)
    ]
    records = [
        *baseline,
        record("monday", date(2026, 11, 16), 8 * 60, 3),
        record("wednesday", date(2026, 11, 18), 6 * 60),
    ]

    result = build_weekly_summary(records, week_start, target_hours=8)
    assert result.week_start == week_start
    assert len(result.days) == 7
    assert result.days[0].session_count == 1
    assert result.days[0].duration_minutes == 480
    assert result.days[0].met_goal is True
    assert result.days[1].session_count == 0
    assert result.days[1].duration_minutes is None
    assert result.days[1].score is None
    assert result.days[1].met_goal is None
    assert result.days[2].duration_minutes == 360
    assert result.days[2].met_goal is False
    assert result.average_duration_minutes == 420
    assert result.average_score == (result.days[0].score + result.days[2].score) / 2
    assert result.days_meeting_goal == 1


def test_empty_week_has_null_averages_and_no_goal_days():
    result = build_weekly_summary([], date(2026, 11, 16), target_hours=8)
    assert len(result.days) == 7
    assert all(day.duration_minutes is None for day in result.days)
    assert all(day.score is None for day in result.days)
    assert all(day.met_goal is None for day in result.days)
    assert result.average_duration_minutes is None
    assert result.average_score is None
    assert result.days_meeting_goal == 0
