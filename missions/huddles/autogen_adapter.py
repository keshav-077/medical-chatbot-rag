"""Optional AutoGen huddle. No code execution. Falls back to sequential roles."""

from __future__ import annotations

import logging

from missions.huddles.safety_review import sanitize_lab_text

logger = logging.getLogger(__name__)


def run_autogen_huddle(kind: str, report: str, extracted: str) -> str:
    try:
        from autogen_agentchat.agents import AssistantAgent
        from autogen_agentchat.teams import RoundRobinGroupChat
        from autogen_agentchat.conditions import MaxMessageTermination
    except Exception as exc:
        logger.debug("AutoGen unavailable: %s", exc)
        return ""
    try:
        extractor = AssistantAgent(
            "extractor",
            system_message="List laboratory names and numbers only. No advice.",
        )
        educator = AssistantAgent(
            "educator",
            system_message=(
                "Explain a laboratory report for a patient in India. "
                "Do not diagnose. Do not give a dose. End with three doctor questions."
            ),
        )
        reviewer = AssistantAgent(
            "safety_reviewer",
            system_message=(
                "Reject any diagnosis, dose, or start/stop medicine language. "
                "If the draft is safe, repeat it. Otherwise rewrite without those claims."
            ),
        )
        team = RoundRobinGroupChat(
            [extractor, educator, reviewer],
            termination_condition=MaxMessageTermination(6),
        )
        # AgentChat is async; keep this adapter sync-safe via a tiny loop if present.
        import asyncio

        prompt = f"Extracted: {extracted}\nReport:\n{report[:3500]}"
        result = asyncio.run(team.run(task=prompt))
        text = ""
        messages = getattr(result, "messages", None) or []
        if messages:
            text = str(getattr(messages[-1], "content", messages[-1]))
        return sanitize_lab_text(text, "")
    except Exception as exc:
        logger.warning("AutoGen %s huddle failed: %s", kind, exc)
        return ""
