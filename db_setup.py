"""Create tables, add columns on existing SQLite/Postgres databases, seed medicines."""

import logging
from pathlib import Path

from sqlalchemy import inspect, text

from models import db

logger = logging.getLogger(__name__)

_MESSAGE_COLUMNS = {
    "citations_json": "TEXT",
    "risk_level": "VARCHAR(32)",
    "trace_id": "VARCHAR(80)",
    "intent": "VARCHAR(32)",
}


def ensure_schema():
    uri = str(db.engine.url)
    if uri.startswith("sqlite"):
        database = db.engine.url.database
        if database and database != ":memory:":
            Path(database).parent.mkdir(parents=True, exist_ok=True)
    db.create_all()
    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())
    if "message" in tables:
        existing = {col["name"] for col in inspector.get_columns("message")}
        for name, ddl in _MESSAGE_COLUMNS.items():
            if name not in existing:
                db.session.execute(text(f"ALTER TABLE message ADD COLUMN {name} {ddl}"))
                logger.info("Added message.%s", name)
        db.session.commit()


def seed_if_empty():
    from ingestion.pipeline import run_ingest
    from models import DrugMonograph

    if DrugMonograph.query.count() == 0:
        run_ingest()
