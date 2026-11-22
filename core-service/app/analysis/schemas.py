from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class AnalysisSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ScoreBreakdownOut(AnalysisSchema):
    duration_score: float
    consistency_score: float | None
    quality_score: float | None


class LatestScoreOut(AnalysisSchema):
    session_id: str
    score: int
    breakdown: ScoreBreakdownOut
    deviation_minutes: float | None


class SleepScoreOut(AnalysisSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "latest": {
                        "sessionId": "c0a80101-0000-4000-8000-000000000002",
                        "score": 82,
                        "breakdown": {
                            "durationScore": 100,
                            "consistencyScore": 75,
                            "qualityScore": 75,
                        },
                        "deviationMinutes": 45,
                    },
                    "weeklyAverage": 79.5,
                    "sessionCount": 12,
                }
            ]
        }
    )
    latest: LatestScoreOut | None
    weekly_average: float | None
    session_count: int


class PatternOut(AnalysisSchema):
    type: Literal["inconsistent_schedule", "late_night_repeat", "sleep_debt"]
    severity: Literal["info", "warning"]
    message: str


class PatternsOut(AnalysisSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "patternsAvailable": True,
                    "minSessions": 3,
                    "patterns": [
                        {
                            "type": "late_night_repeat",
                            "severity": "info",
                            "message": "Jam tidur larut berulang.",
                        }
                    ],
                    "sleepDebtMinutes": 90,
                    "debtWarning": False,
                }
            ]
        }
    )
    patterns_available: bool
    min_sessions: int
    patterns: list[PatternOut]
    sleep_debt_minutes: int
    debt_warning: bool


class SummaryDayOut(AnalysisSchema):
    date: date
    session_count: int
    duration_minutes: int | None
    score: int | None
    met_goal: bool | None


class WeeklySummaryOut(AnalysisSchema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "weekStart": "2026-11-16",
                    "days": [
                        {
                            "date": "2026-11-16",
                            "sessionCount": 1,
                            "durationMinutes": 480,
                            "score": 82,
                            "metGoal": True,
                        }
                    ],
                    "averageDurationMinutes": 480,
                    "averageScore": 82,
                    "daysMeetingGoal": 1,
                }
            ]
        }
    )
    week_start: date
    days: list[SummaryDayOut]
    average_duration_minutes: float | None
    average_score: float | None
    days_meeting_goal: int
