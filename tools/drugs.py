"""Medicine matching and non-exhaustive interaction notes."""

INTERACTION_PAIRS = (
    (
        "metformin",
        "alcohol",
        "Alcohol with metformin may raise the chance of lactic acidosis. Confirm with a pharmacist.",
    ),
    (
        "ibuprofen",
        "paracetamol",
        "These are sometimes used together for a short time. Do not exceed the amounts on the packs. Confirm with a pharmacist.",
    ),
    (
        "amlodipine",
        "atorvastatin",
        "This pair is commonly prescribed. Your doctor should still review muscle pain or swelling. Confirm with a pharmacist.",
    ),
    (
        "azithromycin",
        "antacid",
        "Some antacids can affect how azithromycin is absorbed. Ask a pharmacist about timing.",
    ),
)


def catalog_names(rows) -> list[str]:
    names = []
    for row in rows:
        names.append(row.generic_name)
        brands = row.brand_names or ""
        names.extend(part.strip() for part in brands.split(",") if part.strip())
    return names


def find_monograph(text: str, rows):
    haystack = (text or "").lower()
    best = None
    best_len = 0
    for row in rows:
        for name in catalog_names([row]):
            lowered = name.lower()
            if lowered and lowered in haystack and len(lowered) > best_len:
                best = row
                best_len = len(lowered)
    return best


def interaction_notes(asked_name: str, other_names: list[str]) -> list[str]:
    asked = (asked_name or "").lower()
    others = [name.lower() for name in other_names if name]
    notes = []
    for left, right, note in INTERACTION_PAIRS:
        left_in_profile = any(left in other for other in others)
        right_in_profile = any(right in other for other in others)
        pair = (left in asked and right_in_profile) or (right in asked and left_in_profile)
        if pair:
            notes.append(note)
    return notes
