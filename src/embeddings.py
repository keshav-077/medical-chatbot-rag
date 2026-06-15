"""
Multi-provider embedding system with automatic fallback.
Priority: Jina AI → HuggingFace

Both providers use 768-dimensional embeddings for consistent vector search.
If Jina fails (rate limit, downtime), HuggingFace takes over seamlessly.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv, find_dotenv

# Load environment variables - use find_dotenv to locate the .env file
# override=True ensures we get the latest values
load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Base class for embedding providers."""

    def __init__(self, name: str, dimensions: int):
        self.name = name
        self.dimensions = dimensions
        self.embeddings = None  # LangChain-compatible embeddings instance

    def get_embeddings(self):
        """Return the LangChain embeddings instance."""
        return self.embeddings


class JinaEmbeddingProvider(EmbeddingProvider):
    """
    Jina AI Embeddings (Primary)
    - Model: jina-embeddings-v3
    - 1024 dimensions
    - Free tier: 10M tokens/month
    - Optimized for retrieval tasks
    """

    def __init__(self):
        super().__init__("Jina AI", 1024)

        from langchain_community.embeddings import JinaEmbeddings

        api_key = os.getenv("JINA_API_KEY")
        if not api_key:
            raise ValueError("JINA_API_KEY not found in environment")

        self.embeddings = JinaEmbeddings(
            jina_api_key=api_key,
            model_name="jina-embeddings-v3",
        )
        logger.info("Jina AI embeddings initialized (1024 dims)")


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """
    HuggingFace Embeddings (Backup)
    - Model: sentence-transformers/all-MiniLM-L6-v2
    - 384 dimensions
    - Free tier: unlimited with rate limits
    - Via HuggingFace Inference API
    """

    def __init__(self):
        super().__init__("HuggingFace", 384)

        from langchain_huggingface import HuggingFaceEndpointEmbeddings

        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            raise ValueError("HUGGINGFACE_API_KEY not found in environment")

        self.embeddings = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            huggingfacehub_api_token=api_key,
        )
        logger.info("HuggingFace embeddings initialized (384 dims)")


class EmbeddingManager:
    """
    Smart embedding manager with automatic fallback.
    Priority: Jina AI → HuggingFace

    Usage:
        manager = get_embedding_manager()
        embeddings = manager.get_embeddings()  # For vector stores
    """

    def __init__(self):
        self.providers = self._initialize_providers()

        if not self.providers:
            raise ValueError(
                "No embedding providers configured. "
                "Set at least one of: JINA_API_KEY, HUGGINGFACE_API_KEY in .env"
            )

        self.active_provider = self.providers[0]
        logger.info(f"Primary embedding provider: {self.active_provider.name}")

    def _initialize_providers(self):
        """Initialize all available providers, in priority order."""
        providers = []

        # Priority 1: Jina AI (fast and accurate)
        jina_key = os.getenv("JINA_API_KEY")
        logger.info(f"JINA_API_KEY present: {bool(jina_key)}")
        if jina_key:
            try:
                providers.append(JinaEmbeddingProvider())
                logger.info("✅ Jina AI embeddings available")
            except Exception as e:
                logger.warning(f"⚠️ Jina AI failed to initialize: {e}")

        # Priority 2: HuggingFace (fallback)
        hf_key = os.getenv("HUGGINGFACE_API_KEY")
        logger.info(f"HUGGINGFACE_API_KEY present: {bool(hf_key)}")
        if hf_key:
            try:
                providers.append(HuggingFaceEmbeddingProvider())
                logger.info("✅ HuggingFace embeddings available")
            except Exception as e:
                logger.warning(f"⚠️ HuggingFace failed to initialize: {e}")

        return providers

    def get_embeddings(self):
        """
        Get the active embeddings instance.
        Returns a LangChain-compatible embeddings instance.
        """
        if not self.active_provider:
            raise RuntimeError("No embedding provider available")

        return self.active_provider.get_embeddings()

    def fallback_to_next(self):
        """Switch to the next available provider."""
        current_index = self.providers.index(self.active_provider)
        if current_index + 1 < len(self.providers):
            self.active_provider = self.providers[current_index + 1]
            logger.info(f"Switched embedding provider to {self.active_provider.name}")
            return True
        return False


# ============================================================
# Factory function
# ============================================================

_manager_instance: Optional[EmbeddingManager] = None


def get_embedding_manager() -> EmbeddingManager:
    """
    Get the singleton embedding manager with fallback support.
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = EmbeddingManager()
    return _manager_instance


def get_embeddings():
    """
    Backward-compatible function to get embeddings.
    Returns the active embeddings instance from the manager.
    """
    manager = get_embedding_manager()
    return manager.get_embeddings()
