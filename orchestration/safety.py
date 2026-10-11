"""Emergency screening that runs before any medical generation."""

import re

DISCLAIMER = (
    "This is educational information for India, not a diagnosis, prescription, "
    "or instruction to start, stop, or change a medicine. Confirm with a doctor "
    "or pharmacist."
)

EMERGENCY_PATTERNS = [
    r"chest pain",
    r"heart attack",
    r"can'?t breathe",
    r"cannot breathe",
    r"difficulty breathing",
    r"shortness of breath",
    r"\bstroke\b",
    r"face droop",
    r"slurred speech",
    r"suicid",
    r"kill myself",
    r"want to die",
    r"severe bleeding",
    r"unconscious",
    r"not breathing",
    r"\bseizure\b",
    r"anaphyla",
    r"\boverdose\b",
    r"coughing blood",
    r"vomiting blood",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in EMERGENCY_PATTERNS]


def is_emergency(text: str) -> bool:
    if not text:
        return False
    return any(p.search(text) for p in _COMPILED)


def emergency_answer() -> str:
    return (
        "This may be an emergency. I will not give casual medical advice.\n\n"
        "In India, call 112 for emergency services or 108 for an ambulance now. "
        "If you are thinking about suicide, call Tele-MANAS at 14416 or 1-800-891-4416.\n\n"
        "Go to the nearest hospital emergency department. Do not wait for a chat reply."
    )


def safety_node(state: dict) -> dict:
    message = state.get("message") or ""
    if is_emergency(message):
        return {
            "skip_rag": True,
            "intent": "emergency",
            "risk_level": "emergency",
            "answer": emergency_answer(),
            "citations": [],
            "disclaimer": "Emergency guidance only. Call local emergency services.",
            "map_payload": {},
        }
    return {
        "skip_rag": False,
        "risk_level": state.get("risk_level") or "info",
        "disclaimer": DISCLAIMER,
    }
