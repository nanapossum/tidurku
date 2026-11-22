from datetime import date, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select

from app.identity.models import User
from app.seed import DEMO_ACCOUNT_EMAILS, SEED_ACCOUNT_EMAIL, main, seed_data
from app.security import verify_password
from app.tracking.models import SleepSession
from app.config import settings


def test_seed_twice_is_idempotent_and_creates_expected_scenarios(db):
    seed_today = date(2026, 11, 22)
    password = "seed-test-password"

    seed_data(db, password, seed_today)
    seed_data(db, password, seed_today)

    users = db.scalars(select(User).order_by(User.email)).all()
    assert len(users) == 7
    assert {user.email for user in users} == {
        SEED_ACCOUNT_EMAIL,
        *DEMO_ACCOUNT_EMAILS,
    }

    primary = db.scalar(select(User).where(User.email == SEED_ACCOUNT_EMAIL))
    assert primary is not None
    assert primary.age == 21
    assert primary.city == "Bandung"
    assert verify_password(password, primary.password_hash)
    primary_sessions = db.scalars(
        select(SleepSession).where(SleepSession.user_id == primary.id)
    ).all()
    assert len(primary_sessions) == 14

    ordered = sorted(primary_sessions, key=lambda session: session.end_at)
    durations = [
        (session.end_at - session.start_at).total_seconds() / 60
        for session in ordered
    ]
    assert durations[-3:] == [330, 330, 330]
    local_timezone = ZoneInfo(settings.timezone)
    assert len(
        {session.end_at.astimezone(local_timezone).date() for session in ordered}
    ) == 14
    assert db.query(SleepSession).count() == 20

    yesterday = seed_today - timedelta(days=1)
    demo_users = db.scalars(
        select(User).where(User.email.in_(DEMO_ACCOUNT_EMAILS))
    ).all()
    for demo in demo_users:
        sessions = db.scalars(
            select(SleepSession).where(SleepSession.user_id == demo.id)
        ).all()
        assert len(sessions) == 1
        assert sessions[0].end_at.astimezone(local_timezone).date() == yesterday


def test_seed_password_is_required_before_opening_database(monkeypatch):
    monkeypatch.delenv("SEED_PASSWORD", raising=False)

    with pytest.raises(SystemExit, match="SEED_PASSWORD wajib"):
        main()
