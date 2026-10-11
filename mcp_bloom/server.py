"""FastMCP server. Public tools are query-only. PHI tools need BLOOM_MCP_TOKEN."""

from __future__ import annotations

import os
import sys


def _authorized() -> bool:
    expected = os.getenv("BLOOM_MCP_TOKEN") or ""
    if not expected:
        return False
    return os.getenv("BLOOM_MCP_CLIENT_TOKEN") == expected


def _user_id() -> int | None:
    if not _authorized():
        return None
    raw = os.getenv("BLOOM_MCP_USER_ID") or ""
    try:
        return int(raw)
    except ValueError:
        return None


def build_server():
    from mcp.server.fastmcp import FastMCP

    from mcp_bloom.registry import (
        find_nearby_care,
        get_my_meds,
        get_profile,
        guard_query,
        lookup_drug,
        safety_screen,
        search_medical_knowledge,
        tool_json,
    )
    from mcp_bloom.sources.aqi import get_aqi
    from mcp_bloom.sources.notices import list_safety_notices
    from mcp_bloom.sources.pubmed import search_pubmed

    server = FastMCP("bloom")

    @server.tool()
    def bloom_safety_screen(text: str) -> str:
        """Screen a message for emergency patterns before any medical tool."""
        return tool_json(safety_screen(text), "bloom_safety_screen")

    @server.tool()
    def bloom_lookup_drug(query: str) -> str:
        """Look up an India monograph by generic or brand name."""
        screen = safety_screen(query)
        if screen.get("emergency"):
            return tool_json(screen, "bloom_lookup_drug")
        return tool_json(lookup_drug(query), "bloom_lookup_drug")

    @server.tool()
    def bloom_search_medical_knowledge(query: str) -> str:
        """Semantic search over Bloom's medical library. Query terms only."""
        screen = safety_screen(query)
        if screen.get("emergency"):
            return tool_json(screen, "bloom_search_medical_knowledge")
        return tool_json(search_medical_knowledge(query), "bloom_search_medical_knowledge")

    @server.tool()
    def bloom_find_nearby_care(lat: float, lng: float, kind: str = "hospital") -> str:
        """Find hospitals, pharmacies, or doctors near a coordinate."""
        return tool_json(find_nearby_care(lat, lng, kind), "bloom_find_nearby_care")

    @server.tool()
    def bloom_list_safety_notices(drug: str = "") -> str:
        """List local India educational safety notices. Drug name optional."""
        blocked, safe_drug = guard_query(drug)
        if blocked:
            return tool_json(blocked, "bloom_list_safety_notices")
        return tool_json(list_safety_notices(safe_drug), "bloom_list_safety_notices")

    @server.tool()
    def bloom_get_aqi(lat: float, lng: float) -> str:
        """Open-Meteo AQI for a coordinate. Do not send names or lab values."""
        return tool_json(get_aqi(lat, lng), "bloom_get_aqi")

    @server.tool()
    def bloom_search_pubmed(query: str) -> str:
        """PubMed title search. Send a drug or symptom term only."""
        blocked, safe_query = guard_query(query)
        if blocked:
            return tool_json(blocked, "bloom_search_pubmed")
        return tool_json(search_pubmed(safe_query), "bloom_search_pubmed")

    @server.tool()
    def bloom_get_my_meds() -> str:
        """User medication list. Requires BLOOM_MCP_TOKEN and BLOOM_MCP_USER_ID."""
        if not _authorized():
            return tool_json({"error": "unauthorized"}, "bloom_get_my_meds")
        return tool_json(get_my_meds(_user_id()), "bloom_get_my_meds")

    @server.tool()
    def bloom_get_profile() -> str:
        """User health profile. Requires BLOOM_MCP_TOKEN and BLOOM_MCP_USER_ID."""
        if not _authorized():
            return tool_json({"error": "unauthorized"}, "bloom_get_profile")
        return tool_json(get_profile(_user_id()), "bloom_get_profile")

    return server


def main() -> None:
    # Flask app context so SQLAlchemy tools can query.
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app import app

    with app.app_context():
        build_server().run()


if __name__ == "__main__":
    main()
