"""Medicine card crew: identify, check profile, scan interactions, write a card."""

from __future__ import annotations

from mcp_bloom.registry import interaction_scan, lookup_drug
from mcp_bloom.sources.notices import list_safety_notices
from models import UserMedication, db
from orchestration.safety import DISCLAIMER
from services.notify import notify


def run_med_card(user_id: int, payload: dict) -> dict:
    message = (payload or {}).get("message") or ""
    name = (payload or {}).get("name") or ""
    drug = lookup_drug(name or message)
    generic = drug.get("generic_name") if drug.get("found") else (name or _guess_name(message))
    if payload.get("auto_add") and generic:
        _maybe_add_med(user_id, generic)
    notes = interaction_scan(generic or message, user_id)
    notices = list_safety_notices(generic or "")
    freshness = ""
    if drug.get("found"):
        freshness = f"{drug.get('source')} · {drug.get('document_date')}"
        body = (
            f"{drug['generic_name'].title()}\n"
            f"Also called: {drug.get('brand_names') or '—'}\n\n"
            f"Used for: {drug.get('uses') or 'See the pack or a pharmacist.'}\n\n"
            f"Warnings: {drug.get('warnings') or 'Confirm with a pharmacist.'}\n\n"
            f"Interactions:\n" + "\n".join(f"- {note}" for note in notes) + "\n\n"
            f"Freshness: {freshness}\n\n"
            "I did not change any dose. Confirm with a doctor or pharmacist.\n\n"
            + DISCLAIMER
        )
    else:
        body = (
            f"I noted {generic or 'that medicine'} on your list.\n\n"
            f"Interactions:\n" + "\n".join(f"- {note}" for note in notes) + "\n\n"
            + DISCLAIMER
        )
    if payload.get("auto_add"):
        body = f"Added {generic or 'the medicine'} to your meds. Reply undo med if that was wrong.\n\n" + body
    notify(user_id, body, kind="med_card", href="/meds", payload={"drug": generic})
    return {
        "summary": body,
        "drug": generic,
        "notices": notices,
        "freshness": freshness,
    }


def _guess_name(message: str) -> str:
    words = [part.strip(".,") for part in (message or "").split() if len(part) > 3]
    return words[-1] if words else ""


def _maybe_add_med(user_id: int, name: str) -> None:
    exists = UserMedication.query.filter_by(user_id=user_id, name=name).first()
    if exists:
        return
    db.session.add(UserMedication(user_id=user_id, name=name, dose="", frequency=""))
    db.session.commit()
