"""Weekly digest crew: labs, interactions, notices, one next action."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mcp_bloom.registry import get_my_meds, interaction_scan
from mcp_bloom.sources.notices import list_safety_notices
from models import AppointmentRequest, LabResult
from orchestration.safety import DISCLAIMER
from services.notify import notify


def run_digest(user_id: int, payload: dict | None = None) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=7)
    labs = (
        LabResult.query.filter_by(user_id=user_id)
        .filter(LabResult.created_at >= since)
        .order_by(LabResult.created_at.desc())
        .all()
    )
    meds = get_my_meds(user_id)
    flags = []
    for med in meds:
        flags.extend(interaction_scan(med["name"], user_id)[:2])
    notices = []
    for med in meds:
        notices.extend(list_safety_notices(med["name"]))
    upcoming = (
        AppointmentRequest.query.filter_by(user_id=user_id)
        .order_by(AppointmentRequest.created_at.desc())
        .first()
    )
    next_action = "Upload a lab PDF or tell Bloom how you have been feeling."
    if upcoming:
        next_action = (
            f"Call about your {upcoming.specialty or 'clinic'} draft"
            f"{' at ' + upcoming.place_name if upcoming.place_name else ''}."
        )
    elif labs:
        next_action = "Take the latest lab explanation and your questions to a clinician."
    elif meds:
        next_action = "Ask a pharmacist to review the medicines on your Bloom list."
    lab_bit = "\n".join(f"- {(row.summary or '')[:180]}" for row in labs[:3]) or "- No new labs this week."
    notice_bit = "\n".join(
        f"- {row.get('source')}: {row.get('message')}" for row in notices[:4]
    ) or "- No matching safety notices."
    flag_bit = "\n".join(f"- {item}" for item in dict.fromkeys(flags)[:6]) or "- No catalogued interaction flags."
    body = (
        "Weekly Bloom digest\n\n"
        f"Labs:\n{lab_bit}\n\n"
        f"Medicine notes:\n{flag_bit}\n\n"
        f"Safety notices:\n{notice_bit}\n\n"
        f"Next action: {next_action}\n\n"
        + DISCLAIMER
    )
    notify(user_id, body, kind="digest", href="/", payload={"next_action": next_action})
    return {"summary": body, "next_action": next_action}
