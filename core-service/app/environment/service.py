import logging
from collections.abc import Sequence
from datetime import date, datetime, timedelta
from math import sqrt
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..analysis.service import score_sessions
from ..config import settings
from ..identity.models import User
from ..tracking import repository
from ..tracking.models import SleepSession
from .models import CityLocationCache, NightTemperatureCache
from .openmeteo import (
    CityLocation,
    NightTemperature,
    OpenMeteoAdapter,
    OpenMeteoError,
)


logger = logging.getLogger(__name__)
MIN_REQUIRED = 7
DISCLAIMER = (
    "Hasil ini hanya menggambarkan korelasi, bukan bukti pengaruh langsung "
    "atau saran medis."
)
_FACTOR_LABELS = {
    "temperature": "suhu malam",
    "caffeine": "konsumsi kafein",
    "screen": "durasi penggunaan layar",
}


def pearson_correlation(
    pairs: Sequence[tuple[float, float]],
) -> float | None:
    if len(pairs) < 2:
        return None
    x_values, y_values = zip(*pairs)
    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    x_deviations = [value - x_mean for value in x_values]
    y_deviations = [value - y_mean for value in y_values]
    x_variance = sum(value * value for value in x_deviations)
    y_variance = sum(value * value for value in y_deviations)
    if x_variance == 0 or y_variance == 0:
        return None
    covariance = sum(
        x_value * y_value
        for x_value, y_value in zip(x_deviations, y_deviations)
    )
    result = covariance / sqrt(x_variance * y_variance)
    return round(max(-1.0, min(1.0, result)), 6)


def _finding(factor: str, correlation: float | None) -> dict[str, object]:
    if correlation is None:
        return {
            "factor": factor,
            "correlation": None,
            "direction": "netral",
            "message": "Data belum cukup atau tidak memiliki variasi untuk menghitung korelasi.",
        }

    if abs(correlation) < 0.3:
        message = (
            f"Belum terlihat hubungan yang jelas antara {_FACTOR_LABELS[factor]} "
            "dan skor tidur."
        )
        direction = "netral"
    else:
        direction = "positif" if correlation > 0 else "negatif"
        message = (
            f"Kecenderungan {direction} teramati antara {_FACTOR_LABELS[factor]} "
            "dan skor tidur."
        )
    return {
        "factor": factor,
        "correlation": correlation,
        "direction": direction,
        "message": message,
    }


def _cached_temperatures(
    db: Session,
    city_key: str,
    wake_dates: set[date],
) -> dict[date, float]:
    if not wake_dates:
        return {}
    rows = db.scalars(
        select(NightTemperatureCache).where(
            NightTemperatureCache.city_key == city_key,
            NightTemperatureCache.date.in_(wake_dates),
        )
    ).all()
    return {row.date: row.avg_c for row in rows}


def _save_location(db: Session, location: CityLocation) -> None:
    cached = db.get(CityLocationCache, location.city_key)
    if cached is None:
        db.add(
            CityLocationCache(
                city_key=location.city_key,
                lat=location.lat,
                lon=location.lon,
            )
        )
    else:
        cached.lat = location.lat
        cached.lon = location.lon
    db.commit()


def _save_temperatures(
    db: Session,
    city_key: str,
    temperatures: Sequence[NightTemperature],
) -> None:
    for temperature in temperatures:
        cache_key = (city_key, temperature.date)
        cached = db.get(NightTemperatureCache, cache_key)
        if cached is None:
            db.add(
                NightTemperatureCache(
                    city_key=city_key,
                    date=temperature.date,
                    avg_c=temperature.avg_c,
                )
            )
        else:
            cached.avg_c = temperature.avg_c
    if temperatures:
        db.commit()


def _get_temperature_data(
    db: Session,
    user: User,
    wake_dates: set[date],
    adapter: OpenMeteoAdapter,
) -> dict[date, float]:
    city = user.city.strip() if user.city else ""
    if not city or not wake_dates:
        return {}

    city_key = city.casefold()
    cached_temperatures = _cached_temperatures(db, city_key, wake_dates)
    missing_dates = wake_dates - cached_temperatures.keys()
    if not missing_dates:
        return cached_temperatures

    cached_location = db.get(CityLocationCache, city_key)
    try:
        if cached_location is None:
            location = adapter.geocode(city_key, city)
            _save_location(db, location)
        else:
            location = CityLocation(
                city_key=city_key,
                lat=cached_location.lat,
                lon=cached_location.lon,
            )
        fetched = adapter.night_temperatures(location, missing_dates)
        _save_temperatures(db, city_key, fetched)
    except OpenMeteoError:
        logger.warning(
            "Open-Meteo data unavailable; using cached temperatures if present."
        )

    return _cached_temperatures(db, city_key, wake_dates)


def get_environment_insights(
    db: Session,
    user: User,
    adapter: OpenMeteoAdapter,
) -> dict[str, object]:
    local_timezone = ZoneInfo(settings.timezone)
    today = datetime.now(local_timezone).date()
    sessions = repository.list_by_wake_date(
        db,
        user.id,
        today - timedelta(days=30),
        today,
    )
    wake_dates = {
        session.end_at.astimezone(local_timezone).date()
        for session in sessions
    }
    temperatures = _get_temperature_data(db, user, wake_dates, adapter)
    scores = score_sessions(db, user, sessions)

    pairs: dict[str, list[tuple[float, float]]] = {
        "temperature": [],
        "caffeine": [],
        "screen": [],
    }
    sample_sessions = 0
    for session in sessions:
        score = scores.get(session.id)
        if score is None:
            continue
        wake_date = session.end_at.astimezone(local_timezone).date()
        values: dict[str, float | None] = {
            "temperature": temperatures.get(wake_date),
            "caffeine": (
                float(session.caffeine) if session.caffeine is not None else None
            ),
            "screen": (
                float(session.screen_minutes)
                if session.screen_minutes is not None
                else None
            ),
        }
        has_factor_data = False
        for factor, value in values.items():
            if value is not None:
                pairs[factor].append((value, float(score)))
                has_factor_data = True
        if has_factor_data:
            sample_sessions += 1

    findings = [
        _finding(factor, pearson_correlation(pairs[factor]))
        for factor in ("temperature", "caffeine", "screen")
    ]
    return {
        "available": sample_sessions >= MIN_REQUIRED,
        "sample_size": sample_sessions,
        "min_required": MIN_REQUIRED,
        "temperature_available": bool(temperatures),
        "findings": findings,
        "disclaimer": DISCLAIMER,
    }
