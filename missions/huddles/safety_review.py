"""Reject diagnosis, dosing, and start/stop-medicine language."""

from __future__ import annotations

import re

DIAGNOSIS = re.compile(
    r"\b(you have|you are diagnosed|this means you have|this confirms|"
    r"you suffer from|the diagnosis is)\b",
    re.IGNORECASE,
)
DOSE = re.compile(
    r"\b(take|consume|start|stop|increase|decrease)\s+\d+(?:\.\d+)?\s*(?:mg|ml|mcg)\b",
    re.IGNORECASE,
)
PRESCRIBE = re.compile(
    r"\b(start taking|stop taking|i prescribe|you should take)\b",
    re.IGNORECASE,
)


def review_lab_text(text: str) -> tuple[bool, str]:
    """Return (approved, reason). Tests call this with fixture dialogue."""
    body = text or ""
    if DIAGNOSIS.search(body):
        return False, "Diagnosis language is not allowed."
    if DOSE.search(body):
        return False, "Dosing instructions are not allowed."
    if PRESCRIBE.search(body):
        return False, "Start or stop medicine language is not allowed."
    return True, "ok"


def sanitize_lab_text(text: str, fallback: str) -> str:
    approved, _reason = review_lab_text(text)
    if approved:
        return text
    return fallback
