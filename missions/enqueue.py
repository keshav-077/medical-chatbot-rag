"""Queue a Mission row and optionally run it inline in development."""

from __future__ import annotations

import json
import logging
import os

from models import Mission, db

logger = logging.getLogger(__name__)


def inline_missions_enabled() -> bool:
    flag = os.getenv("BLOOM_INLINE_MISSIONS")
    if flag == "1":
        return True
    if flag == "0":
        return False
    return os.getenv("FLASK_ENV", "development") != "production"


def enqueue_mission(
    kind: str,
    user_id: int | None,
    payload: dict | None = None,
    dedupe_key: str | None = None,
) -> Mission | None:
    if not user_id:
        return None
    row = None
    if dedupe_key:
        existing = Mission.query.filter_by(dedupe_key=dedupe_key).first()
        if existing and existing.status == "failed":
            existing.status = "queued"
            existing.payload_json = json.dumps(payload or {})
            existing.result_json = ""
            db.session.commit()
            row = existing
        elif existing:
            return existing
    if row is None:
        row = Mission(
            user_id=user_id,
            kind=kind,
            payload_json=json.dumps(payload or {}),
            status="queued",
            dedupe_key=dedupe_key,
        )
        db.session.add(row)
        try:
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            logger.warning("Mission enqueue conflict for %s: %s", dedupe_key, exc)
            if dedupe_key:
                return Mission.query.filter_by(dedupe_key=dedupe_key).first()
            return None
    if inline_missions_enabled():
        try:
            from missions.runner import run_one_mission

            run_one_mission(row.id)
            db.session.refresh(row)
        except Exception as exc:
            logger.exception("Inline mission %s failed: %s", row.id, exc)
    return row


def maybe_enqueue_after_turn(user_id: int | None, message: str, result: dict) -> list[Mission]:
    from missions.triggers import missions_for_turn

    intent = (result or {}).get("intent") or "general"
    queued = []
    for spec in missions_for_turn(message, intent, user_id):
        row = enqueue_mission(
            spec["kind"],
            user_id,
            payload=spec.get("payload") or {},
            dedupe_key=spec.get("dedupe_key"),
        )
        if row is not None:
            queued.append(row)
    return queued
