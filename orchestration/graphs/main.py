"""Supervisor graph: safety, intent, specialist node, verifier."""

import logging

from langgraph.graph import END, StateGraph

from models import DrugMonograph
from orchestration.graphs.appointment import appointment_node
from orchestration.graphs.care_find import care_node
from orchestration.graphs.common import general_node, verify_node
from orchestration.graphs.lab import lab_node
from orchestration.graphs.medication import medication_node
from orchestration.graphs.symptom import symptom_node
from orchestration.guardrails import preview_for_log
from orchestration.intent import classify_intent
from orchestration.safety import is_emergency, safety_node
from orchestration.state import BloomState
from services.observability import start_trace
from tools.drugs import catalog_names

logger = logging.getLogger(__name__)
_graph = None


def route_node(state: dict) -> dict:
    forced = (state.get("extra") or {}).get("intent")
    if forced:
        return {"intent": forced}
    try:
        names = catalog_names(DrugMonograph.query.all())
    except Exception as exc:
        logger.warning("Catalog lookup failed: %s", exc)
        names = []
    return {"intent": classify_intent(state.get("message") or "", names)}


def _after_safety(state: dict) -> str:
    if state.get("skip_rag"):
        return "end"
    return "route"


def _pick(state: dict) -> str:
    intent = state.get("intent") or "general"
    if intent not in {"general", "medication", "symptom", "lab", "care", "appointment"}:
        return "general"
    return intent


def build_graph():
    graph = StateGraph(BloomState)
    graph.add_node("safety", safety_node)
    graph.add_node("route", route_node)
    graph.add_node("general", general_node)
    graph.add_node("medication", medication_node)
    graph.add_node("symptom", symptom_node)
    graph.add_node("lab", lab_node)
    graph.add_node("care", care_node)
    graph.add_node("appointment", appointment_node)
    graph.add_node("verify", verify_node)
    graph.set_entry_point("safety")
    graph.add_conditional_edges("safety", _after_safety, {"end": END, "route": "route"})
    graph.add_conditional_edges(
        "route",
        _pick,
        {
            "general": "general",
            "medication": "medication",
            "symptom": "symptom",
            "lab": "lab",
            "care": "care",
            "appointment": "appointment",
        },
    )
    for name in ("general", "medication", "symptom", "lab", "care", "appointment"):
        graph.add_edge(name, "verify")
    graph.add_edge("verify", END)
    return graph.compile()


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_turn(message: str, user_id: int | None = None, extra: dict | None = None, request_id: str = "") -> dict:
    logged = message or ""
    if logged and not is_emergency(logged):
        logged = preview_for_log(logged)
    trace = start_trace(
        "bloom.turn",
        user_id,
        {"message": logged[:500]},
        request_id=request_id,
    )
    extra = dict(extra or {})
    if user_id and extra.get("lat") is None:
        try:
            from services.location import get_user_location

            coords = get_user_location(user_id)
            if coords:
                extra["lat"], extra["lng"] = coords
        except Exception:
            pass
    state = {
        "message": message or "",
        "user_id": user_id,
        "extra": extra,
        "lab_text": extra.get("lab_text") or "",
        "request_id": request_id,
        "citations": [],
        "trace_id": trace.trace_id,
    }
    try:
        result = get_graph().invoke(state)
    except Exception as exc:
        logger.exception("Graph failed")
        result = {
            "answer": f"The assistant hit an error: {exc}",
            "citations": [],
            "risk_level": "info",
            "intent": "general",
            "disclaimer": "",
            "trace_id": trace.trace_id,
        }
    result["trace_id"] = result.get("trace_id") or trace.trace_id
    trace.end(
        output={"intent": result.get("intent"), "risk_level": result.get("risk_level")},
        metadata={"request_id": request_id},
    )
    return result
