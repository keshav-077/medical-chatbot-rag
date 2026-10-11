"""General RAG and shared verify step."""

from orchestration.llm import complete
from orchestration.safety import DISCLAIMER
from src.prompt import system_prompt
from tools.rag import search_knowledge
import re

_DOSE = re.compile(r"\b(?:take|consume)\s+\d+(?:\.\d+)?\s*mg\b", re.IGNORECASE)


def general_node(state: dict) -> dict:
    question = state.get("message") or ""
    citations = search_knowledge(question)
    context = "\n\n".join(item["excerpt"] for item in citations) or "No retrieved context."
    system = system_prompt.replace("{context}", context)
    answer = complete(system, question)
    if not answer:
        answer = (
            "I could not reach a language model. Add OPENROUTER_API_KEY or GROQ_API_KEY. "
            "Retrieved library excerpts are listed when search is available."
        )
    return {
        "intent": "general",
        "answer": answer,
        "citations": citations,
        "context": context,
        "risk_level": "info",
        "disclaimer": DISCLAIMER,
    }


def verify_node(state: dict) -> dict:
    if state.get("intent") == "emergency":
        return {}
    answer = state.get("answer") or ""
    context = (state.get("context") or "").lower()
    disclaimer = state.get("disclaimer") or DISCLAIMER
    if state.get("intent") == "medication":
        def _keep_or_strip(match: re.Match) -> str:
            phrase = match.group(0)
            if phrase.lower() in context:
                return phrase
            return "Follow the dose printed on your prescription or pack"

        answer = _DOSE.sub(_keep_or_strip, answer)
        if "not exhaustive" not in answer.lower():
            answer += "\n\nInteraction notes are not exhaustive."
        if "pharmacist" not in disclaimer.lower():
            disclaimer += " Confirm medicines with a pharmacist."
    if not state.get("citations") and state.get("intent") in ("general", "medication", "symptom"):
        if "no library excerpt" not in answer.lower():
            answer += "\n\nNo library excerpt was retrieved for part of this reply."
    if disclaimer not in answer:
        answer = answer.rstrip() + "\n\n" + disclaimer
    return {
        "answer": answer,
        "disclaimer": disclaimer,
        "risk_level": state.get("risk_level") or "info",
    }
