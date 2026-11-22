import logging
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SleepSessionRecorded:
    user_id: str
    session_id: str
    action: str


@dataclass(frozen=True)
class SleepScoreCalculated:
    user_id: str
    session_id: str = ""
    score: int = 0


@dataclass(frozen=True)
class SleepDebtDetected:
    user_id: str
    debt_hours: float = 0
    consecutive_days: int = 0


@dataclass(frozen=True)
class SleepGoalUpdated:
    user_id: str
    target_hours: float
    bedtime: str


EventType = TypeVar("EventType")
EventHandler = Callable[[Any, Session], None]
_subscribers: dict[type[Any], list[EventHandler]] = {}


def subscribe(
    event_type: type[EventType],
    handler: Callable[[EventType, Session], None],
) -> None:
    handlers = _subscribers.setdefault(event_type, [])
    if handler not in handlers:
        handlers.append(handler)


def publish(event: object, db: Session) -> None:
    for handler in _subscribers.get(type(event), []):
        try:
            handler(event, db)
        except Exception:
            logger.exception("Event handler failed for %s", type(event).__name__)


def clear_subscribers() -> None:
    _subscribers.clear()
