"""Optional CrewAI runner. Missions keep working if the package is missing."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def run_crewai_roles(name: str, roles: list[tuple[str, str, str]]) -> str:
    try:
        from crewai import Agent, Crew, Process, Task
    except Exception as exc:
        logger.debug("CrewAI unavailable: %s", exc)
        return ""
    try:
        agents = []
        tasks = []
        for role_name, goal, content in roles:
            agent = Agent(
                role=role_name,
                goal=goal,
                backstory="Educational health guide for people in India. Never diagnose or prescribe.",
                verbose=False,
                allow_delegation=False,
            )
            agents.append(agent)
            tasks.append(
                Task(
                    description=f"{goal}\n\nInput:\n{content[:4000]}",
                    expected_output="Short educational text. No diagnosis. No dose.",
                    agent=agent,
                )
            )
        crew = Crew(agents=agents, tasks=tasks, process=Process.sequential, verbose=False)
        result = crew.kickoff()
        return str(result).strip()
    except Exception as exc:
        logger.warning("CrewAI %s failed: %s", name, exc)
        return ""
