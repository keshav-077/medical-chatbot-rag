"""Guided symptom intake. Educational only."""

from orchestration.llm import complete
from orchestration.safety import DISCLAIMER
from tools.rag import search_knowledge


def symptom_node(state: dict) -> dict:
    question = state.get("message") or ""
    citations = search_knowledge(question)
    context = "\n\n".join(item["excerpt"] for item in citations) or "No retrieved context."
    system = (
        "You are an educational health guide for people in India. "
        "You do not diagnose. Ask up to three short follow-up questions "
        "(onset, severity, red flags). Use the context when it helps. "
        "Keep the reply under 120 words.\n\n"
        f"Context:\n{context}"
    )
    answer = complete(system, question)
    if not answer:
        answer = (
            "I can help you prepare notes for a clinician, and I cannot diagnose this.\n"
            "Please share: when it started, how severe it feels from 1 to 10, "
            "and whether you have chest pain, fainting, or trouble breathing.\n"
            "If any of those are present, call 112 or 108."
        )
    return {
        "intent": "symptom",
        "answer": answer,
        "citations": citations,
        "context": context,
        "risk_level": "caution",
        "disclaimer": DISCLAIMER,
    }
