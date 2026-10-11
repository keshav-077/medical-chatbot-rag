"""Shared state passed through the bloom graph."""

from typing import Any, Optional, TypedDict


class BloomState(TypedDict, total=False):
    user_id: Optional[int]
    message: str
    intent: str
    context: str
    citations: list
    answer: str
    risk_level: str
    disclaimer: str
    skip_rag: bool
    drug_name: str
    trace_id: str
    freshness: str
    map_payload: dict
    lab_text: str
    appointment: dict
    request_id: str
    extra: dict[str, Any]
