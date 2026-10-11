"""Sequential role runner. Same interface as a CrewAI/AutoGen crew when those are absent."""

from __future__ import annotations

from orchestration.llm import complete


def run_roles(roles: list[tuple[str, str, str]], fallback: str = "") -> str:
    """Run (name, system, human) steps. Each step sees the previous output."""
    prior = ""
    last = fallback
    for name, system, human in roles:
        prompt = human
        if prior:
            prompt = f"{human}\n\nPrevious specialist ({name} context):\n{prior[:4000]}"
        answer = complete(system, prompt)
        if answer:
            last = answer
            prior = answer
    return last or fallback
