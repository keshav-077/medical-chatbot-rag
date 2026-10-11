"""In-process tool registry. FastMCP and missions call these same functions."""

from __future__ import annotations

import json
import logging

from mcp_bloom.sources.aqi import get_aqi
from mcp_bloom.sources.notices import list_safety_notices
from mcp_bloom.sources.pubmed import search_pubmed
from orchestration.safety import emergency_answer, is_emergency
from tools.drugs import catalog_names, find_monograph, interaction_notes
from tools.places import search_nearby
from tools.rag import search_knowledge

logger = logging.getLogger(__name__)


def safety_screen(text: str) -> dict:
    if is_emergency(text):
        return {
            "emergency": True,
            "answer": emergency_answer(),
            "risk_level": "emergency",
        }
    return {"emergency": False, "answer": "", "risk_level": "info"}


def lookup_drug(query: str) -> dict:
    from models import DrugMonograph

    rows = DrugMonograph.query.all()
    monograph = find_monograph(query, rows)
    if monograph is None:
        return {"found": False, "names": catalog_names(rows)[:20]}
    return {
        "found": True,
        "generic_name": monograph.generic_name,
        "brand_names": monograph.brand_names,
        "composition": monograph.composition,
        "uses": monograph.uses,
        "warnings": monograph.warnings,
        "interactions": monograph.interactions,
        "source": monograph.source,
        "document_date": monograph.document_date,
    }


def search_medical_knowledge(query: str) -> list[dict]:
    return search_knowledge(query)


def find_nearby_care(lat: float, lng: float, kind: str = "hospital") -> dict:
    return search_nearby(float(lat), float(lng), kind)


def get_my_meds(user_id: int | None) -> list[dict]:
    if not user_id:
        return []
    from models import UserMedication

    rows = UserMedication.query.filter_by(user_id=user_id).all()
    return [{"name": row.name, "dose": row.dose, "frequency": row.frequency} for row in rows]


def get_profile(user_id: int | None) -> dict:
    if not user_id:
        return {}
    from models import UserHealthProfile

    row = UserHealthProfile.query.filter_by(user_id=user_id).first()
    if row is None:
        return {}
    return {
        "allergies": row.allergies or "",
        "conditions": row.conditions or "",
        "notes": row.notes or "",
        "last_lat": row.last_lat,
        "last_lng": row.last_lng,
        "has_calendar": bool(row.google_refresh_token),
    }


def interaction_scan(asked_name: str, user_id: int | None) -> list[str]:
    others = [item["name"] for item in get_my_meds(user_id)]
    notes = list(interaction_notes(asked_name, others))
    profile = get_profile(user_id)
    allergies = (profile.get("allergies") or "").lower()
    conditions = (profile.get("conditions") or "").lower()
    asked = (asked_name or "").lower()
    if asked and asked in allergies:
        notes.append(
            f"Your profile lists something matching {asked_name}. Confirm this medicine with a doctor or pharmacist."
        )
    if asked and any(word in conditions for word in ("kidney", "liver", "pregnancy")):
        notes.append(
            "Your profile mentions a condition that often changes medicine advice. Confirm with a clinician."
        )
    for notice in list_safety_notices(asked_name):
        notes.append(f"{notice.get('source')}: {notice.get('message')}")
    if not notes:
        notes.append("No catalogued pair matched. This check is not exhaustive.")
    return notes


def tool_json(value) -> str:
    return json.dumps(value, default=str)[:8000]
