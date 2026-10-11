"""LLM calls with provider failover. Returns None when no provider works."""

import logging

logger = logging.getLogger(__name__)


def complete(system: str, human: str) -> str | None:
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from src.llm_providers import get_llm_manager

        manager = get_llm_manager()
    except Exception as exc:
        logger.warning("LLM manager unavailable: %s", exc)
        return None

    last_error = None
    for provider in list(manager.providers):
        try:
            response = provider.llm.invoke(
                [SystemMessage(content=system), HumanMessage(content=human)]
            )
            text = response.content if hasattr(response, "content") else str(response)
            manager.active_provider = provider
            return text
        except Exception as exc:
            logger.error("%s failed: %s", provider.name, exc)
            last_error = exc
    logger.error("All LLM providers failed: %s", last_error)
    return None
