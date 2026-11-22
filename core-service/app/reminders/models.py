from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ReminderSetting(Base):
    __tablename__ = "reminder_settings"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    time: Mapped[str] = mapped_column(String(5), nullable=False)
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
