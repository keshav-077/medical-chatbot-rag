"""Medicine answers from the India monograph catalog plus library search."""

from models import DrugMonograph, UserMedication
from orchestration.safety import DISCLAIMER
from tools.drugs import find_monograph, interaction_notes
from tools.rag import search_knowledge


def medication_node(state: dict) -> dict:
    rows = DrugMonograph.query.all()
    monograph = find_monograph(state.get("message") or "", rows)
    if monograph is None:
        return {
            "intent": "medication",
            "answer": (
                "Which medicine should I explain? Give a generic name or a common Indian brand, "
                "for example paracetamol, Crocin, or metformin."
            ),
            "citations": [],
            "risk_level": "info",
            "freshness": "",
            "disclaimer": DISCLAIMER,
            "context": "",
        }
    others = []
    user_id = state.get("user_id")
    if user_id:
        others = [item.name for item in UserMedication.query.filter_by(user_id=user_id).all()]
    notes = interaction_notes(monograph.generic_name, others)
    interaction_text = monograph.interactions or ""
    if notes:
        interaction_text += "\n" + "\n".join(notes)
    interaction_text += "\nThis interaction check is not exhaustive."
    answer = (
        f"{monograph.generic_name.title()}\n"
        f"Also called: {monograph.brand_names}\n\n"
        f"Composition: {monograph.composition}\n\n"
        f"What it is used for: {monograph.uses}\n\n"
        f"Warnings: {monograph.warnings}\n\n"
        f"Interactions: {interaction_text}\n\n"
        f"Source: {monograph.source}. Document date: {monograph.document_date}."
    )
    citations = [
        {
            "source": monograph.source,
            "excerpt": (monograph.composition or "")[:500],
            "document_date": monograph.document_date,
            "section": "composition",
        }
    ]
    citations.extend(search_knowledge(f"{monograph.generic_name} {state.get('message') or ''}")[:2])
    return {
        "intent": "medication",
        "answer": answer,
        "citations": citations,
        "context": f"{monograph.composition}\n{monograph.warnings}\n{monograph.uses}",
        "risk_level": "caution",
        "freshness": f"{monograph.source} · {monograph.document_date}",
        "drug_name": monograph.generic_name,
        "disclaimer": DISCLAIMER,
    }
