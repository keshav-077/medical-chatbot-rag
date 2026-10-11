"""Assisted appointment drafts. Does not book a clinic."""

import re

from orchestration.safety import DISCLAIMER

_SPECIALTIES = (
    "cardiology",
    "dermatology",
    "ent",
    "general physician",
    "gynaecology",
    "orthopedic",
    "pediatrics",
    "pulmonology",
    "psychiatry",
)


def appointment_node(state: dict) -> dict:
    message = state.get("message") or ""
    lowered = message.lower()
    specialty = "general physician"
    for name in _SPECIALTIES:
        if name in lowered:
            specialty = name
            break
    times = re.findall(
        r"\b(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*|\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b",
        lowered,
    )
    preferred = ", ".join(times[:4]) or "next weekday morning"
    script = (
        f"Hello, I would like a {specialty} appointment. "
        f"Reason: {message[:240]}. Preferred time: {preferred}."
    )
    draft = {
        "specialty": specialty,
        "reason": message[:500],
        "preferred_times": preferred,
        "status": "draft",
        "script": script,
    }
    answer = (
        f"I drafted a {specialty} visit. I cannot book the clinic from here.\n\n"
        f"Call script: {script}\n\n"
        "Save this on the Appointments page, then use the phone link from Care Map "
        "if you picked a hospital or clinic."
    )
    return {
        "intent": "appointment",
        "answer": answer,
        "citations": [],
        "appointment": draft,
        "risk_level": "info",
        "disclaimer": DISCLAIMER,
        "context": "",
    }
