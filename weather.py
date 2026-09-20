"""Weather and sample data helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os

import pandas as pd
import requests


DATA_PATH = Path(__file__).resolve().parent / "data" / "sample_data.csv"


def get_current_weather() -> dict:
    """Return a local weather snapshot for offline development."""
    now = datetime.now()
    return {
        "outdoor_temp_c": 31,
        "humidity_percent": 66,
        "rain_probability_percent": 35,
        "air_quality_index": 96,
        "wind_speed_kmh": 14,
        "time_of_day": now.strftime("%H:%M"),
        "weather_condition": "Cloudy",
    }


def get_weather_for_location(latitude: float, longitude: float, provider: str = "Open-Meteo") -> dict:
    """Fetch real weather for a latitude/longitude pair."""
    if provider == "AccuWeather":
        api_key = os.getenv("ACCUWEATHER_API_KEY")
        if api_key:
            return _get_accuweather(latitude, longitude, api_key)

    return _get_open_meteo(latitude, longitude)


def load_sample_dataset() -> pd.DataFrame:
    """Load sample environmental scenarios."""
    dataset = pd.read_csv(DATA_PATH)
    if "rain_expected" in dataset.columns and "rain_probability_percent" not in dataset.columns:
        dataset["rain_probability_percent"] = dataset["rain_expected"].map(lambda value: 85 if _to_bool(value) else 10)
    if "time_of_day" not in dataset.columns:
        dataset["time_of_day"] = pd.to_datetime(dataset["timestamp"]).dt.strftime("%H:%M")
    return dataset


def _get_open_meteo(latitude: float, longitude: float) -> dict:
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,rain,wind_speed_10m,weather_code",
        "hourly": "precipitation_probability",
        "forecast_days": 1,
        "timezone": "auto",
    }
    air_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    air_params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "us_aqi",
        "timezone": "auto",
    }

    weather_response = requests.get(weather_url, params=weather_params, timeout=10)
    weather_response.raise_for_status()
    weather_payload = weather_response.json()
    current = weather_payload.get("current", {})

    rain_probability = _nearest_hourly_value(
        weather_payload.get("hourly", {}),
        current.get("time"),
        "precipitation_probability",
        default=0,
    )

    try:
        air_response = requests.get(air_url, params=air_params, timeout=10)
        air_response.raise_for_status()
        air_payload = air_response.json()
        air_quality_index = air_payload.get("current", {}).get("us_aqi", 75)
    except requests.RequestException:
        air_quality_index = 75

    return {
        "outdoor_temp_c": float(current.get("temperature_2m", 28)),
        "humidity_percent": float(current.get("relative_humidity_2m", 60)),
        "rain_probability_percent": float(rain_probability),
        "air_quality_index": float(air_quality_index or 75),
        "wind_speed_kmh": float(current.get("wind_speed_10m", 0)),
        "time_of_day": _time_from_api(current.get("time")),
        "weather_condition": weather_code_to_condition(current.get("weather_code"), rain_probability),
        "provider": "Open-Meteo",
        "latitude": latitude,
        "longitude": longitude,
    }


def _get_accuweather(latitude: float, longitude: float, api_key: str) -> dict:
    location_response = requests.get(
        "https://dataservice.accuweather.com/locations/v1/cities/geoposition/search",
        params={"apikey": api_key, "q": f"{latitude},{longitude}"},
        timeout=10,
    )
    location_response.raise_for_status()
    location_key = location_response.json()["Key"]

    current_response = requests.get(
        f"https://dataservice.accuweather.com/currentconditions/v1/{location_key}",
        params={"apikey": api_key, "details": "true"},
        timeout=10,
    )
    current_response.raise_for_status()
    current = current_response.json()[0]

    forecast_response = requests.get(
        f"https://dataservice.accuweather.com/forecasts/v1/hourly/1hour/{location_key}",
        params={"apikey": api_key, "metric": "true"},
        timeout=10,
    )
    forecast_response.raise_for_status()
    forecast = forecast_response.json()[0]

    now = datetime.now()
    return {
        "outdoor_temp_c": float(current["Temperature"]["Metric"]["Value"]),
        "humidity_percent": float(current.get("RelativeHumidity", 60)),
        "rain_probability_percent": float(forecast.get("PrecipitationProbability", 0)),
        "air_quality_index": 75,
        "wind_speed_kmh": float(current.get("Wind", {}).get("Speed", {}).get("Metric", {}).get("Value", 0)),
        "time_of_day": now.strftime("%H:%M"),
        "weather_condition": _accuweather_condition(str(current.get("WeatherText", ""))),
        "provider": "AccuWeather",
        "latitude": latitude,
        "longitude": longitude,
    }


def _nearest_hourly_value(hourly: dict, current_time: str | None, key: str, default: float) -> float:
    values = hourly.get(key) or []
    times = hourly.get("time") or []
    if not values:
        return default
    if current_time in times:
        return values[times.index(current_time)]
    return values[0]


def weather_code_to_condition(code: object, rain_probability: float = 0) -> str:
    """Convert Open-Meteo weather code into a simple display condition."""
    try:
        weather_code = int(code)
    except (TypeError, ValueError):
        return "Rainy" if rain_probability >= 60 else "Cloudy"

    if weather_code in {0, 1}:
        return "Sunny"
    if weather_code in {2, 3, 45, 48}:
        return "Cloudy"
    if weather_code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}:
        return "Rainy"
    if weather_code in {71, 73, 75, 77, 85, 86}:
        return "Cloudy"
    return "Rainy" if rain_probability >= 60 else "Cloudy"


def infer_condition_from_readings(rain_probability: float, humidity_percent: float, wind_speed_kmh: float) -> str:
    """Infer Sunny, Cloudy, or Rainy for manual and sample readings."""
    if rain_probability >= 60:
        return "Rainy"
    if humidity_percent >= 75 or rain_probability >= 35 or wind_speed_kmh >= 35:
        return "Cloudy"
    return "Sunny"


def _accuweather_condition(text: str) -> str:
    normalized = text.lower()
    if "rain" in normalized or "storm" in normalized or "shower" in normalized:
        return "Rainy"
    if "sun" in normalized or "clear" in normalized:
        return "Sunny"
    return "Cloudy"


def _time_from_api(value: str | None) -> str:
    if not value:
        return datetime.now().strftime("%H:%M")
    try:
        return datetime.fromisoformat(value).strftime("%H:%M")
    except ValueError:
        return datetime.now().strftime("%H:%M")


def _to_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}
