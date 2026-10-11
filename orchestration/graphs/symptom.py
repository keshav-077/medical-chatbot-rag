"""Guided symptom intake. Educational only."""

from mcp_bloom.sources.aqi import get_aqi, is_respiratory
from orchestration.llm import complete
from orchestration.safety import DISCLAIMER
from services.location import get_user_location
from tools.rag import search_knowledge


def symptom_node(state: dict) -> dict:
    question = state.get("message") or ""
    citations = search_knowledge(question)
    context = "\n\n".join(item["excerpt"] for item in citations) or "No retrieved context."
    aqi_line = ""
    coords = get_user_location(state.get("user_id"))
    extra = state.get("extra") or {}
    if coords is None and extra.get("lat") is not None and extra.get("lng") is not None:
        coords = (float(extra["lat"]), float(extra["lng"]))
    if coords and is_respiratory(question):
        aqi = get_aqi(coords[0], coords[1])
        if aqi.get("summary"):
            aqi_line = aqi["summary"]
            context += "\n\nAir quality: " + aqi_line
    system = (
        "You are an educational health guide for people in India. "
        "You do not diagnose. Ask up to three short follow-up questions "
        "(onset, severity, red flags). Use the context when it helps. "
        "If air quality is mentioned, say it may irritate symptoms but is not a diagnosis. "
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
    if aqi_line and aqi_line not in (answer or ""):
        answer = (answer or "").rstrip() + "\n\n" + aqi_line
    return {
        "intent": "symptom",
        "answer": answer,
        "citations": citations,
        "context": context,
        "risk_level": "caution",
        "disclaimer": DISCLAIMER,
    }
