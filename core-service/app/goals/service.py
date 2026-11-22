from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import AppError
from ..events import SleepGoalUpdated, publish
from ..identity.models import User
from .defaults import DEFAULT_BEDTIME, default_target, healthy_range
from .models import SleepGoal
from .schemas import GoalOut, HealthyRangeOut, GoalUpdateIn


def get_goal(db: Session, user: User) -> GoalOut:
    minimum, maximum = healthy_range(user.age)
    goal = db.get(SleepGoal, user.id)
    if goal is None:
        target_hours = default_target(user.age)
        bedtime = DEFAULT_BEDTIME
        is_default = True
    else:
        target_hours = goal.target_hours
        bedtime = goal.bedtime
        is_default = False
    return GoalOut(
        target_hours=target_hours,
        bedtime=bedtime,
        healthy_range=HealthyRangeOut(min=minimum, max=maximum),
        is_default=is_default,
    )


def update_goal(db: Session, user: User, data: GoalUpdateIn) -> GoalOut:
    minimum, maximum = healthy_range(user.age)
    if (
        not minimum <= data.target_hours <= maximum
        and not data.confirm_out_of_range
    ):
        raise AppError(
            422,
            "TARGET_OUT_OF_RANGE",
            f"Target harus berada dalam rentang sehat {minimum}–{maximum} jam, "
            "atau kirim confirmOutOfRange=true untuk mengonfirmasi.",
        )

    goal = db.get(SleepGoal, user.id)
    if goal is None:
        goal = SleepGoal(
            user_id=user.id,
            target_hours=data.target_hours,
            bedtime=data.bedtime,
        )
        db.add(goal)
    else:
        goal.target_hours = data.target_hours
        goal.bedtime = data.bedtime

    db.commit()
    db.refresh(goal)
    publish(
        SleepGoalUpdated(
            user_id=user.id,
            target_hours=goal.target_hours,
            bedtime=goal.bedtime,
        ),
        db,
    )
    return get_goal(db, user)
