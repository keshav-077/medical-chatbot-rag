"""Keyword intent routing. Runs after the emergency check."""

CARE_WORDS = (
    "near me",
    "nearby",
    "hospital",
    "pharmacy",
    "chemist",
    "medical store",
    "doctor near",
    "clinic near",
    "find a doctor",
    "find hospital",
)
APPT_WORDS = (
    "appointment",
    "book a",
    "schedule a",
    "see a doctor",
    "book visit",
)
LAB_WORDS = (
    "lab report",
    "blood test",
    "my report",
    "hemoglobin",
    "hba1c",
    "lab result",
    "explain my lab",
    "explain this report",
)
MED_WORDS = (
    "tablet",
    "capsule",
    "medicine",
    "medication",
    "side effect",
    "composition",
    "interaction",
    "what is in",
    "drug",
)
SYMPTOM_WORDS = (
    "cough",
    "fever",
    "pain",
    "symptom",
    "breath",
    "nausea",
    "headache",
    "rash",
    "dizzy",
)


def classify_intent(message: str, catalog_names: list[str] | None = None) -> str:
    text = (message or "").lower()
    if any(word in text for word in APPT_WORDS):
        return "appointment"
    if any(word in text for word in CARE_WORDS):
        return "care"
    if any(word in text for word in LAB_WORDS):
        return "lab"
    for name in catalog_names or []:
        if name and name.lower() in text:
            return "medication"
    if any(word in text for word in MED_WORDS):
        return "medication"
    if any(word in text for word in SYMPTOM_WORDS):
        return "symptom"
    return "general"
