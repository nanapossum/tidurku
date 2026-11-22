from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import math
from collections.abc import Iterable

import httpx

from ..config import settings


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
USER_AGENT = "TidurKu/1.0 (tugas-kuliah)"


class OpenMeteoError(RuntimeError):
    pass


@dataclass(frozen=True)
class CityLocation:
    city_key: str
    lat: float
    lon: float


@dataclass(frozen=True)
class NightTemperature:
    date: date
    avg_c: float


class OpenMeteoAdapter:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=5.0)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def geocode(self, city_key: str, city_name: str) -> CityLocation:
        payload = self._request_json(
            GEOCODING_URL,
            {
                "name": city_name,
                "count": 1,
                "country_code": "ID",
            },
        )
        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list):
            raise OpenMeteoError("Format respons geocoding Open-Meteo tidak valid.")
        if not results or not isinstance(results[0], dict):
            raise OpenMeteoError("Lokasi kota tidak ditemukan di Open-Meteo.")

        result = results[0]
        latitude = self._number(result.get("latitude"))
        longitude = self._number(result.get("longitude"))
        if latitude is None or longitude is None:
            raise OpenMeteoError("Koordinat geocoding Open-Meteo tidak valid.")
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise OpenMeteoError("Koordinat geocoding Open-Meteo di luar rentang.")
        return CityLocation(city_key=city_key, lat=latitude, lon=longitude)

    def night_temperatures(
        self,
        location: CityLocation,
        wake_dates: Iterable[date],
    ) -> list[NightTemperature]:
        requested_dates = set(wake_dates)
        if not requested_dates:
            return []

        payload = self._request_json(
            FORECAST_URL,
            {
                "latitude": location.lat,
                "longitude": location.lon,
                "hourly": "temperature_2m",
                "past_days": 30,
                "timezone": settings.timezone,
            },
        )
        hourly = payload.get("hourly") if isinstance(payload, dict) else None
        timestamps = hourly.get("time") if isinstance(hourly, dict) else None
        temperatures = (
            hourly.get("temperature_2m") if isinstance(hourly, dict) else None
        )
        if (
            not isinstance(timestamps, list)
            or not isinstance(temperatures, list)
            or len(timestamps) != len(temperatures)
        ):
            raise OpenMeteoError("Format data hourly Open-Meteo tidak valid.")

        hourly_values: list[tuple[datetime, float | None]] = []
        for timestamp, temperature in zip(timestamps, temperatures):
            if not isinstance(timestamp, str):
                raise OpenMeteoError("Timestamp hourly Open-Meteo tidak valid.")
            try:
                local_time = datetime.fromisoformat(timestamp)
            except ValueError as exc:
                raise OpenMeteoError(
                    "Timestamp hourly Open-Meteo tidak valid."
                ) from exc
            if local_time.tzinfo is not None:
                raise OpenMeteoError(
                    "Timestamp hourly Open-Meteo harus berupa waktu lokal."
                )
            if temperature is not None and self._number(temperature) is None:
                raise OpenMeteoError("Nilai suhu Open-Meteo tidak valid.")
            hourly_values.append(
                (local_time, None if temperature is None else float(temperature))
            )

        nights: list[NightTemperature] = []
        for wake_date in sorted(requested_dates):
            night_start = datetime.combine(wake_date - timedelta(days=1), time(22))
            night_end = datetime.combine(wake_date, time(6))
            readings = [
                temperature
                for timestamp, temperature in hourly_values
                if night_start <= timestamp < night_end and temperature is not None
            ]
            if readings:
                nights.append(
                    NightTemperature(
                        date=wake_date,
                        avg_c=sum(readings) / len(readings),
                    )
                )
        return nights

    def _request_json(self, url: str, params: dict[str, object]) -> object:
        for attempt in range(2):
            try:
                response = self._client.get(
                    url,
                    params=params,
                    timeout=5.0,
                    headers={"User-Agent": USER_AGENT},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500 and attempt == 0:
                    continue
                raise OpenMeteoError("Permintaan Open-Meteo gagal.") from exc
            except httpx.HTTPError as exc:
                if attempt == 0:
                    continue
                raise OpenMeteoError("Open-Meteo tidak dapat dijangkau.") from exc

            try:
                payload = response.json()
            except ValueError as exc:
                raise OpenMeteoError("Respons Open-Meteo bukan JSON yang valid.") from exc
            if not isinstance(payload, dict):
                raise OpenMeteoError("Format respons Open-Meteo tidak valid.")
            return payload

        raise OpenMeteoError("Permintaan Open-Meteo gagal setelah retry.")

    @staticmethod
    def _number(value: object) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        number = float(value)
        return number if math.isfinite(number) else None
