import os
from datetime import date, datetime, time, timedelta
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models_registry  # noqa: F401
from .config import settings
from .database import SessionLocal
from .identity.models import User
from .security import hash_password, verify_password
from .tracking.models import SleepSession


SEED_ACCOUNT_EMAIL = "uji@tidurku.id"
DEMO_ACCOUNT_EMAILS = tuple(
    f"demo{index:02d}@tidurku.id" for index in range(1, 7)
)
_SEED_NAMESPACE = "https://tidurku.id/seed/"


def _stable_id(value: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"{_SEED_NAMESPACE}{value}"))


def _get_or_create_user(
    db: Session,
    email: str,
    name: str,
    password: str,
    age: int,
) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            id=_stable_id(f"user:{email}"),
            name=name,
            email=email,
            password_hash=hash_password(password),
            age=age,
            city="Bandung",
        )
        db.add(user)
        db.flush()
    else:
        user.name = name
        user.age = age
        user.city = "Bandung"
        if not verify_password(password, user.password_hash):
            user.password_hash = hash_password(password)
    return user


def _session_times(wake_date: date, schedule: str) -> tuple[datetime, datetime]:
    timezone = ZoneInfo(settings.timezone)
    if schedule == "short":
        start = datetime.combine(wake_date - timedelta(days=1), time(23, 30))
        end = datetime.combine(wake_date, time(5, 0))
    elif schedule == "inconsistent":
        start = datetime.combine(wake_date - timedelta(days=1), time(19, 0))
        end = datetime.combine(wake_date, time(3, 0))
    else:
        start = datetime.combine(wake_date - timedelta(days=1), time(22, 30))
        end = datetime.combine(wake_date, time(6, 30))
    return start.replace(tzinfo=timezone), end.replace(tzinfo=timezone)


def _upsert_session(
    db: Session,
    user: User,
    wake_date: date,
    schedule: str,
    quality: int,
    caffeine: int,
    screen_minutes: int,
) -> None:
    start_at, end_at = _session_times(wake_date, schedule)
    session_id = _stable_id(f"session:{user.email}:{wake_date.isoformat()}")
    session = db.get(SleepSession, session_id)
    values = {
        "user_id": user.id,
        "start_at": start_at,
        "end_at": end_at,
        "quality": quality,
        "stress": ("Rendah", "Sedang", "Tinggi")[quality % 3],
        "caffeine": caffeine,
        "screen_minutes": screen_minutes,
        "notes": None,
    }
    if session is None:
        db.add(SleepSession(id=session_id, **values))
        return
    for field, value in values.items():
        setattr(session, field, value)


def seed_data(db: Session, password: str, today: date | None = None) -> None:
    password_bytes = password.encode("utf-8")
    if not 8 <= len(password_bytes) <= 72:
        raise ValueError("SEED_PASSWORD harus berukuran 8–72 byte UTF-8.")

    local_today = today or datetime.now(ZoneInfo(settings.timezone)).date()
    yesterday = local_today - timedelta(days=1)
    test_user = _get_or_create_user(
        db,
        SEED_ACCOUNT_EMAIL,
        "Akun Uji TidurKu",
        password,
        21,
    )

    for index in range(14):
        wake_date = yesterday - timedelta(days=13 - index)
        schedule = (
            "short"
            if index >= 11
            else "inconsistent"
            if index == 5
            else "consistent"
        )
        _upsert_session(
            db,
            test_user,
            wake_date,
            schedule,
            quality=2 + index % 4,
            caffeine=index % 3,
            screen_minutes=30 + index * 10,
        )

    for index, email in enumerate(DEMO_ACCOUNT_EMAILS, start=1):
        demo_user = _get_or_create_user(
            db,
            email,
            f"Pengguna Demo {index}",
            password,
            21,
        )
        _upsert_session(
            db,
            demo_user,
            yesterday,
            "consistent",
            quality=1 + (index - 1) % 5,
            caffeine=(index - 1) % 3,
            screen_minutes=45 * index,
        )

    db.commit()


def main() -> None:
    password = os.environ.get("SEED_PASSWORD")
    if not password:
        raise SystemExit("SEED_PASSWORD wajib diatur untuk menjalankan seed.")
    if not 8 <= len(password.encode("utf-8")) <= 72:
        raise SystemExit("SEED_PASSWORD harus berukuran 8–72 byte UTF-8.")

    db = SessionLocal()
    try:
        seed_data(db, password)
    finally:
        db.close()


if __name__ == "__main__":
    main()
