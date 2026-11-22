from sqlalchemy.orm import Session

from ..goals.schemas import GoalOut
from ..goals.service import get_goal
from ..identity.models import User
from .models import ReminderSetting
from .schemas import ReminderOut, ReminderUpdateIn


def reminder_time_for_bedtime(bedtime: str) -> str:
    hours, minutes = (int(part) for part in bedtime.split(":"))
    total_minutes = (hours * 60 + minutes - 30) % (24 * 60)
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def default_reminder_time(goal: GoalOut) -> str:
    return reminder_time_for_bedtime(goal.bedtime)


def _as_output(
    setting: ReminderSetting | None,
    goal: GoalOut,
) -> ReminderOut:
    if setting is None:
        return ReminderOut(
            enabled=True,
            time=default_reminder_time(goal),
            is_custom=False,
        )
    return ReminderOut(
        enabled=setting.enabled,
        time=setting.time,
        is_custom=setting.is_custom,
    )


def get_reminder(db: Session, user: User) -> ReminderOut:
    setting = db.get(ReminderSetting, user.id)
    return _as_output(setting, get_goal(db, user))


def update_reminder(
    db: Session,
    user: User,
    data: ReminderUpdateIn,
) -> ReminderOut:
    goal = get_goal(db, user)
    setting = db.get(ReminderSetting, user.id)
    if setting is None:
        setting = ReminderSetting(
            user_id=user.id,
            enabled=True,
            time=default_reminder_time(goal),
            is_custom=False,
        )
        db.add(setting)

    setting.enabled = data.enabled
    if "time" in data.model_fields_set:
        if data.time is None:
            setting.time = default_reminder_time(goal)
            setting.is_custom = False
        else:
            setting.time = data.time
            setting.is_custom = True

    db.commit()
    db.refresh(setting)
    return _as_output(setting, goal)
