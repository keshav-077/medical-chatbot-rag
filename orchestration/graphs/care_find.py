"""Find hospitals, pharmacies, and doctors near a coordinate."""

import re

from orchestration.safety import DISCLAIMER
from tools.places import search_nearby

_COORDS = re.compile(r"(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)")


def _kind(message: str) -> str:
    text = message.lower()
    if "pharmac" in text or "chemist" in text or "medical store" in text:
        return "pharmacy"
    if "doctor" in text or "clinic" in text:
        return "doctor"
    return "hospital"


def care_node(state: dict) -> dict:
    message = state.get("message") or ""
    extra = state.get("extra") or {}
    lat = extra.get("lat")
    lng = extra.get("lng")
    if lat is None or lng is None:
        found = _COORDS.search(message)
        if found:
            lat = float(found.group(1))
            lng = float(found.group(2))
    kind = extra.get("kind") or _kind(message)
    if lat is None or lng is None:
        return {
            "intent": "care",
            "answer": (
                "Open the Care Map and allow location, or send a message with coordinates "
                "like 28.6139, 77.2090. I can then list nearby hospitals, pharmacies, or doctors in India."
            ),
            "citations": [],
            "map_payload": {},
            "risk_level": "info",
            "disclaimer": DISCLAIMER,
        }
    payload = search_nearby(float(lat), float(lng), kind)
    if payload.get("error"):
        answer = f"I could not search places: {payload['error']}"
    elif not payload.get("places"):
        answer = "No places came back for that spot. Try a larger town or another category."
    else:
        lines = [f"Nearby {kind}s, closest first:"]
        for place in payload["places"][:5]:
            distance = place.get("distance_km")
            dist = f"{distance} km" if distance is not None else "distance unknown"
            phone = f", {place['phone']}" if place.get("phone") else ""
            lines.append(f"- {place['name']} ({dist}{phone})")
        lines.append("Open the Care Map to see pins and directions. This is not a medical referral.")
        answer = "\n".join(lines)
    return {
        "intent": "care",
        "answer": answer,
        "citations": [],
        "map_payload": payload,
        "risk_level": "info",
        "disclaimer": DISCLAIMER,
        "context": "",
    }
