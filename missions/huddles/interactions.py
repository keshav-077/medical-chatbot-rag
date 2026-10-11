"""Pharmacist / profile / skeptic huddle for 'can I take X with…'."""

from __future__ import annotations

from mcp_bloom.registry import get_profile, interaction_scan, lookup_drug
from missions.huddles.safety_review import sanitize_lab_text
from orchestration.graphs.common import verify_node
from orchestration.safety import DISCLAIMER
from services.notify import notify


def run_interaction_huddle(user_id: int, payload: dict) -> dict:
    message = (payload or {}).get("message") or ""
    drug = lookup_drug(message)
    name = drug.get("generic_name") if drug.get("found") else message[:80]
    notes = interaction_scan(name, user_id)
    profile = get_profile(user_id)
    freshness = ""
    if drug.get("found"):
        freshness = f"{drug.get('source')} · {drug.get('document_date')}"
    fallback = (
        f"Interaction check for {name}\n\n"
        + "\n".join(f"- {note}" for note in notes)
        + "\n\nThis is not exhaustive. I cannot tell you to start or stop a medicine.\n"
        f"Profile allergies noted: {profile.get('allergies') or 'none listed'}.\n"
        f"Freshness: {freshness or 'catalog lookup incomplete'}.\n\n"
        + DISCLAIMER
    )
    published = sanitize_lab_text(fallback, fallback)
    verified = verify_node(
        {
            "intent": "medication",
            "answer": published,
            "context": (drug.get("composition") or "") + " " + (drug.get("warnings") or ""),
            "citations": (
                [{"source": drug.get("source"), "excerpt": (drug.get("composition") or "")[:400]}]
                if drug.get("found")
                else []
            ),
            "disclaimer": DISCLAIMER,
            "risk_level": "caution",
        }
    )
    answer = verified.get("answer") or published
    notify(user_id, answer, kind="interaction", href="/meds", payload={"drug": name})
    return {"summary": answer, "drug": name, "freshness": freshness}
