"""Google Places search for hospitals, pharmacies, and doctors in India."""

import logging
import math
import os

import requests

logger = logging.getLogger(__name__)

KIND_TO_TYPE = {
    "hospital": "hospital",
    "pharmacy": "pharmacy",
    "doctor": "doctor",
}


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _details(place_id: str, api_key: str) -> dict:
    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place_id,
                "fields": "formatted_phone_number,opening_hours",
                "key": api_key,
            },
            timeout=12,
        )
        payload = response.json()
        return payload.get("result") or {}
    except requests.RequestException as exc:
        logger.warning("Place details failed: %s", exc)
        return {}


def search_nearby(lat: float, lng: float, kind: str = "hospital") -> dict:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {
            "error": "GOOGLE_MAPS_API_KEY is not set.",
            "places": [],
            "center": {"lat": lat, "lng": lng},
            "kind": kind,
        }
    gtype = KIND_TO_TYPE.get(kind, "hospital")
    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params={
                "location": f"{lat},{lng}",
                "radius": 8000,
                "type": gtype,
                "key": api_key,
            },
            timeout=15,
        )
        payload = response.json()
    except requests.RequestException as exc:
        return {
            "error": str(exc),
            "places": [],
            "center": {"lat": lat, "lng": lng},
            "kind": kind,
        }
    if payload.get("status") not in ("OK", "ZERO_RESULTS"):
        return {
            "error": payload.get("error_message") or payload.get("status"),
            "places": [],
            "center": {"lat": lat, "lng": lng},
            "kind": kind,
        }
    places = []
    for index, item in enumerate(payload.get("results") or []):
        loc = (item.get("geometry") or {}).get("location") or {}
        plat, plng = loc.get("lat"), loc.get("lng")
        phone = ""
        open_now = None
        hours = item.get("opening_hours") or {}
        if "open_now" in hours:
            open_now = bool(hours.get("open_now"))
        if index < 3 and item.get("place_id"):
            detail = _details(item["place_id"], api_key)
            phone = detail.get("formatted_phone_number") or ""
            if open_now is None and detail.get("opening_hours"):
                open_now = detail["opening_hours"].get("open_now")
        distance = None
        if plat is not None and plng is not None:
            distance = round(_haversine_km(lat, lng, plat, plng), 2)
        places.append(
            {
                "place_id": item.get("place_id"),
                "name": item.get("name"),
                "address": item.get("vicinity") or "",
                "rating": item.get("rating"),
                "phone": phone,
                "lat": plat,
                "lng": plng,
                "open_now": open_now,
                "distance_km": distance,
                "kind": kind,
                "maps_url": "https://www.google.com/maps/search/?api=1&query="
                + requests.utils.quote(item.get("name") or "")
                + f"&query_place_id={item.get('place_id')}",
            }
        )
    places.sort(
        key=lambda row: (
            row["distance_km"] is None,
            row["distance_km"] or 999,
            -(row["rating"] or 0),
        )
    )
    return {
        "error": None,
        "places": places[:12],
        "center": {"lat": lat, "lng": lng},
        "kind": kind,
    }
