"""Lab second opinion: extract → educate → safety review → publish."""

from __future__ import annotations

import json

from missions.huddles.safety_review import review_lab_text, sanitize_lab_text
from missions.roles import run_roles
from models import LabResult, db
from orchestration.graphs.common import verify_node
from orchestration.graphs.lab import parse_lab_rows
from orchestration.safety import DISCLAIMER
from services.notify import notify


def run_lab_review(user_id: int, payload: dict) -> dict:
    lab_text = (payload or {}).get("lab_text") or ""
    document_id = (payload or {}).get("document_id")
    rows = parse_lab_rows(lab_text)
    extracted = ", ".join(f"{row['name']} {row['value']} {row['unit']}" for row in rows[:12])
    fallback = (
        "I extracted the values I could read and will not diagnose you from this report.\n"
        f"Values: {extracted or 'no numeric rows detected'}.\n"
        "Questions for your doctor: What do these values mean for me? "
        "Do I need a repeat test? Is any medicine change needed?\n\n"
        + DISCLAIMER
    )
    educated = _educate(lab_text, extracted, fallback)
    published = sanitize_lab_text(educated, fallback)
    verified = verify_node(
        {
            "intent": "lab",
            "answer": published,
            "context": lab_text[:2000],
            "citations": [{"source": "Uploaded lab report", "excerpt": lab_text[:400]}],
            "disclaimer": DISCLAIMER,
            "risk_level": "caution",
        }
    )
    answer = verified.get("answer") or published
    approved, reason = review_lab_text(answer)
    if not approved:
        answer = fallback
    result = LabResult(
        user_id=user_id,
        document_id=document_id,
        summary=answer,
        rows_json=json.dumps({"rows": rows, "reviewed": True, "review_reason": reason}),
    )
    db.session.add(result)
    db.session.commit()
    notify(
        user_id,
        "Reviewed lab report\n\n" + answer,
        kind="lab_review",
        href="/labs",
        payload={"lab_result_id": result.id, "reviewed": True},
    )
    return {"summary": answer, "rows": rows, "reviewed": True, "lab_result_id": result.id}


def _educate(lab_text: str, extracted: str, fallback: str) -> str:
    try:
        from missions.huddles.autogen_adapter import run_autogen_huddle

        text = run_autogen_huddle("lab", lab_text[:4000], extracted)
        if text:
            return text
    except Exception:
        pass
    return run_roles(
        [
            (
                "extractor",
                "List laboratory names and numbers only. No advice.",
                lab_text[:4000] or extracted,
            ),
            (
                "educator",
                "Explain a laboratory report for a patient in India. "
                "Use only the report. Do not diagnose. End with three questions for a doctor. "
                "Under 180 words.",
                f"Extracted values: {extracted}\nReport:\n{lab_text[:4000]}",
            ),
        ],
        fallback=fallback,
    )
