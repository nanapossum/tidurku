from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SleepRecord:
    id: str
    start_local: datetime
    end_local: datetime
    duration_min: float
    quality: int | None
