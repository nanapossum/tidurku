from sqlalchemy.orm import Session

from ..events import SleepGoalUpdated, subscribe
from .models import ReminderSetting
from .service import reminder_time_for_bedtime


def update_default_reminder_time(event: SleepGoalUpdated, db: Session) -> None:
    setting = db.get(ReminderSetting, event.user_id)
    if setting is None or setting.is_custom:
        return
    setting.time = reminder_time_for_bedtime(event.bedtime)
    db.commit()


def register_handlers() -> None:
    subscribe(SleepGoalUpdated, update_default_reminder_time)
