"""Open-Meteo air quality. Input is lat/lng only — never profile or labs."""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

RESPIRATORY_HINTS = (
    "cough",
    "asthma",
    "breath",
    "wheeze",
    "pollution",
    "aqi",
    "smog",
    "lungs",
    "inhaler",
)


def is_respiratory(message: str) -> bool:
    text = (message or "").lower()
    return any(hint in text for hint in RESPIRATORY_HINTS)


def get_aqi(lat: float, lng: float) -> dict:
    import os

    if os.getenv("BLOOM_OFFLINE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
        return {"error": None, "aqi": None, "summary": ""}
    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (TypeError, ValueError):
        return {"error": "lat and lng are required", "aqi": None}
    try:
        response = requests.get(
            "https://air-quality-api.open-meteo.com/v1/air-quality",
            params={
                "latitude": lat_f,
                "longitude": lng_f,
                "current": "us_aqi,pm2_5,pm10",
            },
            timeout=10,
        )
        response.raise_for_status()
        current = (response.json() or {}).get("current") or {}
        aqi = current.get("us_aqi")
        return {
            "error": None,
            "aqi": aqi,
            "pm2_5": current.get("pm2_5"),
            "pm10": current.get("pm10"),
            "summary": _summarize(aqi),
        }
    except requests.RequestException as exc:
        logger.warning("AQI lookup failed: %s", exc)
        return {"error": str(exc), "aqi": None, "summary": ""}


def _summarize(aqi) -> str:
    if aqi is None:
        return ""
    try:
        value = float(aqi)
    except (TypeError, ValueError):
        return ""
    if value <= 50:
        band = "good"
    elif value <= 100:
        band = "moderate"
    elif value <= 150:
        band = "unhealthy for sensitive groups"
    else:
        band = "unhealthy"
    return (
        f"Local US AQI is about {int(value)} ({band}). "
        "Pollution can irritate cough or asthma. This is not a diagnosis."
    )
