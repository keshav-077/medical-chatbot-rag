"""Decide which missions to queue after a chat turn. No I/O."""

from __future__ import annotations

import re
from datetime import datetime, timezone

VISIT_HINTS = ("doctor", "clinic", "visit", "appointment", "see a", "hospital")
TAKE_MED = re.compile(
    r"\b(i take|i'm taking|i am taking|started taking|started|add(?:ed)?)\b",
    re.IGNORECASE,
)
INTERACTION_HINTS = (
    "can i take",
    "can i use",
    "together with",
    "interaction",
    "with my",
    "along with",
)
UNDO_MED = re.compile(r"^\s*(undo med|stop meds|undo medicine)\s*$", re.IGNORECASE)


def wants_visit_pack(message: str, intent: str) -> bool:
    if intent == "appointment":
        return True
    if intent == "symptom":
        text = (message or "").lower()
        return any(hint in text for hint in VISIT_HINTS)
    return False


def wants_med_card(message: str, intent: str) -> bool:
    if intent != "medication":
        return False
    return bool(TAKE_MED.search(message or ""))


def wants_interaction_huddle(message: str, intent: str) -> bool:
    if intent != "medication":
        return False
    text = (message or "").lower()
    return any(hint in text for hint in INTERACTION_HINTS)


def is_undo_med(message: str) -> bool:
    return bool(UNDO_MED.match(message or ""))


def missions_for_turn(message: str, intent: str, user_id: int | None) -> list[dict]:
    """Return enqueue specs. Empty when there is no user or nothing to automate."""
    if not user_id or intent == "emergency":
        return []
    specs = []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    if wants_visit_pack(message, intent):
        specs.append(
            {
                "kind": "visit_pack",
                "payload": {"message": message, "intent": intent},
                "dedupe_key": f"visit:{user_id}:{stamp}",
            }
        )
    if wants_med_card(message, intent):
        specs.append(
            {
                "kind": "med_card",
                "payload": {"message": message, "auto_add": True},
                "dedupe_key": f"med:{user_id}:{_slug(message)[:40]}:{stamp}",
            }
        )
    if wants_interaction_huddle(message, intent):
        specs.append(
            {
                "kind": "interaction_huddle",
                "payload": {"message": message},
                "dedupe_key": f"ix:{user_id}:{_slug(message)[:40]}:{stamp}",
            }
        )
    return specs


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
