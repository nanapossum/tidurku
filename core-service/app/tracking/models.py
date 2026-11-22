from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4

from ..database import Base, UTCDateTime


class SleepSession(Base):
    __tablename__ = "sleep_sessions"
    __table_args__ = (
        CheckConstraint(
            "quality IS NULL OR quality BETWEEN 1 AND 5",
            name="ck_sleep_sessions_quality",
        ),
        CheckConstraint(
            "stress IS NULL OR stress IN ('Rendah', 'Sedang', 'Tinggi')",
            name="ck_sleep_sessions_stress",
        ),
        CheckConstraint(
            "caffeine IS NULL OR caffeine BETWEEN 0 AND 9999",
            name="ck_sleep_sessions_caffeine",
        ),
        CheckConstraint(
            "screen_minutes IS NULL OR screen_minutes BETWEEN 0 AND 9999",
            name="ck_sleep_sessions_screen_minutes",
        ),
        CheckConstraint(
            "notes IS NULL OR length(notes) <= 500",
            name="ck_sleep_sessions_notes_length",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    end_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stress: Mapped[str | None] = mapped_column(String(10), nullable=True)
    caffeine: Mapped[int | None] = mapped_column(Integer, nullable=True)
    screen_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
