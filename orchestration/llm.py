"""LLM calls with provider failover. Returns None when no provider works."""

import logging

logger = logging.getLogger(__name__)


def complete(system: str, human: str, context: str = "") -> str | None:
    """Call a model. Screens instructions, retrieved context, and the reply first."""
    from orchestration.guardrails import screen_context, screen_output, screen_user_text

    if context:
        original = context
        ctx = screen_context(original)
        if ctx.blocked:
            return ctx.text
        if ctx.text != original and original in (system or ""):
            system = (system or "").replace(original, ctx.text, 1)

    # Local patterns only. The instruction text is trusted; Bedrock content
    # filters on it would block ordinary medical guidance.
    instructions = screen_context(system or "", bedrock=False)
    if instructions.blocked:
        return instructions.text
    system = instructions.text

    user = screen_user_text(human or "")
    if user.blocked:
        return user.text
    human = user.text

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
            if not text:
                return None
            checked = screen_output(text)
            return checked.text
        except Exception as exc:
            logger.error("%s failed: %s", provider.name, exc)
            last_error = exc
    logger.error("All LLM providers failed: %s", last_error)
    return None
