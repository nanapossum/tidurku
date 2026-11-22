from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class CityLocationCache(Base):
    __tablename__ = "city_location"

    city_key: Mapped[str] = mapped_column(String(120), primary_key=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)


class NightTemperatureCache(Base):
    __tablename__ = "night_temperature"

    city_key: Mapped[str] = mapped_column(
        String(120),
        ForeignKey("city_location.city_key", ondelete="CASCADE"),
        primary_key=True,
    )
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    avg_c: Mapped[float] = mapped_column(Float, nullable=False)
