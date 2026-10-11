"""Pinecone retrieval. Lazy so the app can boot without API keys."""

import logging
import os

logger = logging.getLogger(__name__)

_retriever = None
_unavailable = False


def get_retriever():
    global _retriever, _unavailable
    if _retriever is not None or _unavailable:
        return _retriever
    if not os.getenv("PINECONE_API_KEY") or not os.getenv("JINA_API_KEY"):
        _unavailable = True
        return None
    try:
        from langchain_pinecone import Pinecone as PineconeVectorStore
        from src.embeddings import get_embeddings

        embeddings = get_embeddings()
        store = PineconeVectorStore.from_existing_index(
            index_name="medicalbot",
            embedding=embeddings,
        )
        _retriever = store.as_retriever(
            search_type="similarity", search_kwargs={"k": 3}
        )
    except Exception as exc:
        logger.warning("Retriever unavailable: %s", exc)
        _unavailable = True
        return None
    return _retriever


def search_knowledge(query: str) -> list[dict]:
    retriever = get_retriever()
    if not retriever or not query:
        return []
    try:
        docs = retriever.invoke(query)
    except Exception as exc:
        logger.warning("Retrieval failed: %s", exc)
        return []
    citations = []
    for doc in docs:
        meta = getattr(doc, "metadata", None) or {}
        excerpt = (getattr(doc, "page_content", "") or "")[:500]
        citations.append(
            {
                "source": meta.get("source") or meta.get("file_path") or "medicalbot",
                "excerpt": excerpt,
                "document_date": str(meta.get("document_date") or ""),
                "section": str(meta.get("section") or "library"),
            }
        )
    return citations
