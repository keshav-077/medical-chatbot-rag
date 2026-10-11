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

_USER_COLUMNS = {
    "telegram_chat_id": "VARCHAR(32)",
    "telegram_link_token": "VARCHAR(64)",
}

_PROFILE_COLUMNS = {
    "last_lat": "FLOAT",
    "last_lng": "FLOAT",
    "last_located_at": "DATETIME",
}

_NOTIFICATION_COLUMNS = {
    "payload_json": "TEXT",
    "href": "VARCHAR(300)",
}


def _quote_ident(name: str) -> str:
    if db.engine.dialect.name == "postgresql":
        return f'"{name}"'
    return name


def _adapt_ddl(ddl: str) -> str:
    if db.engine.dialect.name == "postgresql":
        return ddl.replace("DATETIME", "TIMESTAMP")
    return ddl


def _add_columns(table: str, columns: dict[str, str], inspector) -> None:
    existing = {col["name"] for col in inspector.get_columns(table)}
    qtable = _quote_ident(table)
    for name, ddl in columns.items():
        if name not in existing:
            col_ddl = _adapt_ddl(ddl)
            db.session.execute(text(f"ALTER TABLE {qtable} ADD COLUMN {name} {col_ddl}"))
            logger.info("Added %s.%s", table, name)


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
        _add_columns("message", _MESSAGE_COLUMNS, inspector)
    if "user" in tables:
        _add_columns("user", _USER_COLUMNS, inspector)
    if "user_health_profile" in tables:
        _add_columns("user_health_profile", _PROFILE_COLUMNS, inspector)
    if "notification" in tables:
        _add_columns("notification", _NOTIFICATION_COLUMNS, inspector)
    db.session.commit()


def seed_if_empty():
    from ingestion.pipeline import run_ingest
    from models import DrugMonograph

    if DrugMonograph.query.count() == 0:
        run_ingest()
