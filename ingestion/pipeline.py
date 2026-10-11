"""Load sources.yaml into DrugMonograph rows and optional Pinecone metadata."""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml

from models import DrugMonograph, IngestJob, db

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]


def _hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_sources() -> list[dict]:
    path = ROOT / "ingestion" / "sources.yaml"
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get("sources") or []


def upsert_monographs(records: list[dict], source_id: str) -> int:
    count = 0
    for record in records:
        name = (record.get("generic_name") or "").strip().lower()
        if not name:
            continue
        blob = json.dumps(record, sort_keys=True)
        digest = _hash(blob)
        row = DrugMonograph.query.filter_by(generic_name=name).first()
        if row is None:
            row = DrugMonograph(generic_name=name)
            db.session.add(row)
        row.brand_names = record.get("brand_names") or ""
        row.composition = record.get("composition") or ""
        row.uses = record.get("uses") or ""
        row.warnings = record.get("warnings") or ""
        row.interactions = record.get("interactions") or ""
        row.source = record.get("source") or source_id
        row.document_date = record.get("document_date") or ""
        row.country = record.get("country") or "IN"
        row.section = record.get("section") or "monograph"
        row.content_hash = digest
        count += 1
    db.session.commit()
    return count


def _try_pinecone(records: list[dict]) -> str:
    try:
        from langchain_core.documents import Document
        from tools.rag import get_retriever
    except Exception as exc:
        return f"pinecone skipped: {exc}"
    retriever = get_retriever()
    if retriever is None:
        return "pinecone skipped: retriever not configured"
    try:
        store = retriever.vectorstore
        docs = []
        for record in records:
            name = (record.get("generic_name") or "").strip().lower()
            if not name:
                continue
            text = "\n".join(
                [
                    record.get("composition") or "",
                    record.get("uses") or "",
                    record.get("warnings") or "",
                    record.get("interactions") or "",
                ]
            )
            docs.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": record.get("source") or "india_seed",
                        "document_date": record.get("document_date") or "",
                        "section": "drug_labels",
                        "country": "IN",
                        "generic_name": name,
                    },
                )
            )
        if docs:
            store.add_documents(docs)
        return f"pinecone upserted {len(docs)}"
    except Exception as exc:
        logger.warning("Pinecone monograph upsert failed: %s", exc)
        return f"pinecone skipped: {exc}"


def run_ingest() -> list[dict]:
    results = []
    for source in load_sources():
        source_id = source.get("id") or "unknown"
        path = ROOT / source.get("path", "")
        detail = ""
        status = "ok"
        digest = ""
        try:
            raw = path.read_text(encoding="utf-8")
            digest = _hash(raw)
            records = json.loads(raw)
            if source_id == "india_seed":
                count = upsert_monographs(records, source_id)
                detail = f"upserted {count} monographs. {_try_pinecone(records)}"
            else:
                detail = f"loaded {len(records)} records from {source_id}"
        except Exception as exc:
            status = "error"
            detail = str(exc)
        job = IngestJob(
            source_id=source_id,
            content_hash=digest,
            status=status,
            detail=detail,
            ran_at=datetime.now(timezone.utc),
        )
        db.session.add(job)
        db.session.commit()
        results.append({"source": source_id, "status": status, "detail": detail})
    return results
