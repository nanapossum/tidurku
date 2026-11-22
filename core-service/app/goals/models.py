from datetime import date, datetime, timezone

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base, UTCDateTime


class SleepGoal(Base):
    __tablename__ = "sleep_goals"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    target_hours: Mapped[float] = mapped_column(Float, nullable=False)
    bedtime: Mapped[str] = mapped_column(String(5), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class RecommendationCompletion(Base):
    __tablename__ = "recommendation_completion"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    code: Mapped[str] = mapped_column(String(80), primary_key=True)
    date_local: Mapped[date] = mapped_column(Date, primary_key=True)
