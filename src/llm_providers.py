"""
Multi-LLM system with automatic fallback.
Priority: OpenRouter → Groq

Both providers use the same model (gpt-oss-120b) for consistent output quality.
If OpenRouter fails (rate limit, downtime), Groq takes over seamlessly.
"""

import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class LLMProvider:
    """Base class for LLM providers."""

    def __init__(self, name: str):
        self.name = name
        self.llm = None  # LangChain-compatible LLM instance

    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter LLM (Primary)
    - Model: openai/gpt-oss-120b:free
    - Free tier: generous limits
    - 128K context window
    - Uses ChatOpenAI with base_url override
    """

    def __init__(self):
        super().__init__("OpenRouter")

        from langchain_openai import ChatOpenAI

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

        self.llm = ChatOpenAI(
            model="openai/gpt-oss-120b:free",
            openai_api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.4,
            max_tokens=500,
            timeout=30,
            default_headers={
                "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8080"),
                "X-Title": "Medical Chatbot RAG",
            },
        )
        logger.info("OpenRouter LLM initialized (gpt-oss-120b:free)")

    def generate(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return response.content


class GroqProvider(LLMProvider):
    """
    Groq LLM (Backup)
    - Model: openai/gpt-oss-120b (same model, Groq's LPU infrastructure)
    - Free: 30 requests/minute
    - 128K context window
    - 500+ tokens/second on Groq's LPU chips
    """

    def __init__(self):
        super().__init__("Groq")

        from langchain_groq import ChatGroq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")

        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            groq_api_key=api_key,
            temperature=0.4,
            max_tokens=500,
            timeout=30,
        )
        logger.info("Groq LLM initialized (gpt-oss-120b)")

    def generate(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return response.content


class LLMManager:
    """
    Smart LLM manager with automatic fallback.
    Priority: OpenRouter → Groq

    Usage:
        manager = get_llm_manager()
        llm = manager.get_llm()          # For LangChain chains
        response = manager.generate(msg)  # Direct generation
    """

    def __init__(self):
        self.providers: List[LLMProvider] = self._initialize_providers()

        if not self.providers:
            raise ValueError(
                "No LLM providers configured. "
                "Set at least one of: OPENROUTER_API_KEY, GROQ_API_KEY in .env"
            )

        self.active_provider = self.providers[0]
        logger.info(f"Primary LLM provider: {self.active_provider.name}")

    def _initialize_providers(self) -> List[LLMProvider]:
        """Initialize all available providers, in priority order."""
        providers = []

        # Priority 1: OpenRouter (current, already working)
        if os.getenv("OPENROUTER_API_KEY"):
            try:
                providers.append(OpenRouterProvider())
                logger.info("✅ OpenRouter LLM available")
            except Exception as e:
                logger.warning(f"⚠️ OpenRouter failed to initialize: {e}")

        # Priority 2: Groq (fast fallback)
        if os.getenv("GROQ_API_KEY"):
            try:
                providers.append(GroqProvider())
                logger.info("✅ Groq LLM available")
            except Exception as e:
                logger.warning(f"⚠️ Groq failed to initialize: {e}")

        return providers

    def generate(self, prompt: str) -> str:
        """Generate a response with automatic fallback."""
        last_error = None

        for provider in self.providers:
            try:
                response = provider.generate(prompt)

                if provider != self.active_provider:
                    logger.info(f"Switched LLM provider to {provider.name}")
                    self.active_provider = provider

                return response
            except Exception as e:
                logger.error(f"{provider.name} generate failed: {e}")
                last_error = e
                continue

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")

    def get_llm(self):
        """
        Get the active LLM instance for LangChain chains.
        Returns a ChatOpenAI or ChatGroq instance that is compatible
        with LangChain's LCEL pipe syntax.
        """
        return self.active_provider.llm


# ============================================================
# Factory function
# ============================================================

_manager_instance: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    """
    Get the singleton LLM manager with fallback support.
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = LLMManager()
    return _manager_instance
