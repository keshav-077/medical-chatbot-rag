"""NCBI E-utilities title search. Query is a drug or symptom term only."""

from __future__ import annotations

import logging
import re

import requests

logger = logging.getLogger(__name__)

_SAFE = re.compile(r"[^a-zA-Z0-9 \-]+")


def search_pubmed(query: str, limit: int = 3) -> list[dict]:
    import os

    if os.getenv("BLOOM_OFFLINE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
        return []
    crumb = _SAFE.sub(" ", query or "").strip()[:80]
    if not crumb:
        return []
    try:
        search = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": crumb,
                "retmax": max(1, min(limit, 5)),
                "retmode": "json",
            },
            timeout=12,
        )
        search.raise_for_status()
        ids = ((search.json().get("esearchresult") or {}).get("idlist")) or []
        if not ids:
            return []
        summary = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
            timeout=12,
        )
        summary.raise_for_status()
        result = (summary.json() or {}).get("result") or {}
        citations = []
        for pmid in ids:
            item = result.get(pmid) or {}
            title = item.get("title") or ""
            if not title:
                continue
            citations.append(
                {
                    "source": f"PubMed {pmid}",
                    "excerpt": title[:500],
                    "document_date": str(item.get("pubdate") or ""),
                    "section": "pubmed",
                }
            )
        return citations
    except requests.RequestException as exc:
        logger.warning("PubMed search failed: %s", exc)
        return []
