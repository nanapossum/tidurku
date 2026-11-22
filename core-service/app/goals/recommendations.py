from collections.abc import Mapping
from typing import Protocol


class GoalLike(Protocol):
    bedtime: str


RECOMMENDATION_CODES = frozenset(
    {
        "track_sleep_3_nights",
        "keep_bedtime_regular",
        "shift_bedtime_earlier",
        "sleep_30_minutes_more",
        "consistent_bedtime_window",
    }
)


def _value(item: object, key: str) -> object:
    if isinstance(item, Mapping):
        return item.get(key)
    return getattr(item, key, None)


def build_recommendations(
    patterns: Mapping[str, object] | None,
    goal: GoalLike,
) -> list[dict[str, object]]:
    """Build simple recommendations; negative shifts mean an earlier bedtime."""
    entries = patterns.get("patterns", ()) if patterns else ()
    available = bool(
        patterns
        and patterns.get(
            "patterns_available",
            patterns.get("patternsAvailable", False),
        )
    )
    recommendations: list[tuple[int, int, dict[str, object]]] = []
    recommendation_by_pattern = {
        "late_night_repeat": {
            "id": "shift_bedtime_earlier",
            "text": "Geser jam tidur 30 menit lebih awal.",
            "shiftMinutes": -30,
        },
        "sleep_debt": {
            "id": "sleep_30_minutes_more",
            "text": "Tambah waktu tidur 30 menit malam ini dengan mulai tidur lebih awal.",
            "shiftMinutes": -30,
        },
        "inconsistent_schedule": {
            "id": "consistent_bedtime_window",
            "text": (
                f"Pertahankan jam tidur sekitar {goal.bedtime}, "
                "dalam rentang 30 menit."
            ),
            "shiftMinutes": 0,
        },
    }
    severity_order = {"warning": 0, "info": 1}

    if available:
        for index, pattern in enumerate(entries):
            pattern_type = _value(pattern, "type")
            recommendation = recommendation_by_pattern.get(pattern_type)
            if recommendation is None:
                continue
            severity = _value(pattern, "severity")
            recommendations.append(
                (
                    severity_order.get(severity, 2),
                    index,
                    {
                        **recommendation,
                        "basedOn": pattern_type,
                        "done": False,
                    },
                )
            )

    if not recommendations:
        recommendations = [
            (
                0,
                0,
                {
                    "id": "track_sleep_3_nights",
                    "text": "Catat waktu tidur selama 3 malam.",
                    "shiftMinutes": 0,
                    "basedOn": "general",
                    "done": False,
                },
            ),
            (
                0,
                1,
                {
                    "id": "keep_bedtime_regular",
                    "text": (
                        f"Jaga jam tidur tetap teratur, sekitar {goal.bedtime}."
                    ),
                    "shiftMinutes": 0,
                    "basedOn": "general",
                    "done": False,
                },
            ),
        ]

    recommendations.sort(key=lambda item: (item[0], item[1]))
    return [item for _, _, item in recommendations[:3]]
