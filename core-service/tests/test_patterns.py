from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.analysis.patterns import analyze_patterns
from app.analysis.records import SleepRecord


LOCAL = ZoneInfo("Asia/Jakarta")


def session(record_id, wake_day, duration_min=480, bedtime_hour=22, bedtime_minute=0):
    wake_date = datetime(2026, 2, wake_day).date()
    start_date = wake_date - timedelta(days=1) if bedtime_hour >= 12 else wake_date
    start = datetime(
        start_date.year,
        start_date.month,
        start_date.day,
        bedtime_hour,
        tzinfo=LOCAL,
    ) + timedelta(minutes=bedtime_minute)
    end = start + timedelta(minutes=duration_min)
    return SleepRecord(record_id, start, end, duration_min, 4)


def pattern_types(result):
    return {pattern.type for pattern in result.patterns}


def test_patterns_unavailable_below_three_sessions():
    result = analyze_patterns([session("one", 1)], target_hours=8)
    assert result.patterns_available is False
    assert result.patterns == ()


def test_inconsistent_pattern_uses_strictly_greater_than_ninety_minutes():
    baseline = [session(f"prior-{day}", day) for day in (1, 2, 3)]
    at_ninety = session("latest", 4, bedtime_minute=90)
    result_at_ninety = analyze_patterns([*baseline, at_ninety], 8)
    assert "inconsistent_schedule" not in pattern_types(result_at_ninety)

    at_ninety_one = session("latest", 4, bedtime_minute=91)
    result_at_ninety_one = analyze_patterns([*baseline, at_ninety_one], 8)
    assert "inconsistent_schedule" in pattern_types(result_at_ninety_one)


def test_late_night_repeat_uses_three_of_seven_bedtime_dates():
    two_late = [
        session("late-1", 3, bedtime_hour=0, bedtime_minute=0),
        session("late-2", 4, bedtime_hour=4, bedtime_minute=59),
        session("regular", 5),
    ]
    assert "late_night_repeat" not in pattern_types(analyze_patterns(two_late, 8))

    three_late = [
        session("late-1", 3, bedtime_hour=0),
        session("late-2", 4, bedtime_hour=2),
        session("late-3", 5, bedtime_hour=4, bedtime_minute=59),
    ]
    assert "late_night_repeat" in pattern_types(analyze_patterns(three_late, 8))

    outside_window = [
        session("late-1", 3, bedtime_hour=0),
        session("late-2", 4, bedtime_hour=2),
        session("not-late", 5, bedtime_hour=5),
    ]
    assert "late_night_repeat" not in pattern_types(
        analyze_patterns(outside_window, 8)
    )


def test_sleep_debt_boundaries_and_three_day_streak():
    two_short_days = [
        session("short-1a", 1, duration_min=2 * 60),
        session("short-1b", 1, duration_min=2 * 60),
        session("short-2", 2, duration_min=5 * 60 + 59),
    ]
    result = analyze_patterns(two_short_days, target_hours=8)
    assert result.debt_warning is False
    assert "sleep_debt" not in pattern_types(result)

    three_short_days = [
        session(f"short-{day}", day, duration_min=5 * 60 + 59)
        for day in (1, 2, 3)
    ]
    result = analyze_patterns(three_short_days, target_hours=8)
    assert result.debt_warning is True
    assert result.sleep_debt_minutes == 3 * (8 * 60 - (5 * 60 + 59))
    assert "sleep_debt" in pattern_types(result)


def test_six_hours_is_not_short_sleep_and_missing_day_breaks_streak():
    six_hour_days = [
        session(f"six-{day}", day, duration_min=6 * 60)
        for day in (1, 2, 3)
    ]
    assert analyze_patterns(six_hour_days, 8).debt_warning is False

    missing_day = [
        session("short-1", 1, duration_min=5 * 60),
        session("short-2", 2, duration_min=5 * 60),
        session("short-4", 4, duration_min=5 * 60),
    ]
    assert analyze_patterns(missing_day, 8).debt_warning is False


def test_sleep_debt_sums_only_recorded_days_in_last_seven_days():
    records = [
        session("old", 1, duration_min=1 * 60),
        session("recent-a", 3, duration_min=7 * 60),
        session("recent-b", 4, duration_min=6 * 60),
        session("recent-c", 5, duration_min=8 * 60),
        session("latest", 8, duration_min=5 * 60),
    ]
    result = analyze_patterns(records, 8)
    assert result.sleep_debt_minutes == 60 + 120 + 180


def test_sleep_debt_and_late_night_use_as_of_window_but_warning_uses_last_data():
    old_short_nights = [
        session(f"short-{day}", day, duration_min=5 * 60, bedtime_hour=1)
        for day in (1, 2, 3)
    ]
    result = analyze_patterns(
        old_short_nights,
        target_hours=8,
        as_of_date=date(2026, 2, 20),
    )
    assert result.sleep_debt_minutes == 0
    assert result.debt_warning is True
    assert "sleep_debt" in pattern_types(result)
    assert "late_night_repeat" not in pattern_types(result)
