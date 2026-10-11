"""Execute queued missions and schedule weekly / upcoming-visit jobs."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from models import AppointmentRequest, Mission, User, db
from services.observability import start_trace

logger = logging.getLogger(__name__)

HANDLERS = {
    "visit_pack": "missions.crews.visit_pack:run_visit_pack",
    "med_card": "missions.crews.med_card:run_med_card",
    "digest": "missions.crews.digest:run_digest",
    "lab_review": "missions.huddles.lab_review:run_lab_review",
    "interaction_huddle": "missions.huddles.interactions:run_interaction_huddle",
}


def run_one_mission(mission_id: int) -> dict:
    row = db.session.get(Mission, mission_id)
    if row is None:
        return {"error": "missing"}
    if row.status == "done":
        try:
            return json.loads(row.result_json or "{}")
        except json.JSONDecodeError:
            return {}
    if row.kind not in HANDLERS:
        row.status = "failed"
        row.result_json = json.dumps({"error": f"unknown kind {row.kind}"})
        db.session.commit()
        return {"error": f"unknown kind {row.kind}"}
    row.status = "running"
    db.session.commit()
    payload = {}
    if row.payload_json:
        try:
            payload = json.loads(row.payload_json)
        except json.JSONDecodeError:
            payload = {}
    trace = start_trace(
        "bloom.mission",
        row.user_id,
        {"kind": row.kind, "mission_id": row.id},
    )
    try:
        handler = _load(HANDLERS[row.kind])
        result = handler(row.user_id, payload) or {}
        row.status = "done"
        row.result_json = json.dumps(result, default=str)
        row.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        trace.end(output={"kind": row.kind, "status": "done"})
        return result
    except Exception as exc:
        logger.exception("Mission %s (%s) failed", row.id, row.kind)
        row.status = "failed"
        row.result_json = json.dumps({"error": str(exc)})
        row.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        trace.end(output={"kind": row.kind, "status": "failed"})
        return {"error": str(exc)}


def run_missions(limit: int = 10) -> dict:
    queued_upcoming_visits()
    queued_weekly_digests()
    processed = 0
    failed = 0
    rows = (
        Mission.query.filter_by(status="queued")
        .order_by(Mission.id.asc())
        .limit(limit)
        .all()
    )
    for row in rows:
        result = run_one_mission(row.id)
        if result.get("error"):
            failed += 1
        else:
            processed += 1
    return {"processed": processed, "failed": failed, "queued": len(rows)}


def queued_upcoming_visits() -> int:
    from missions.enqueue import enqueue_mission

    now = datetime.now(timezone.utc)
    soon = now + timedelta(hours=48)
    created = 0
    rows = AppointmentRequest.query.filter(
        AppointmentRequest.created_at >= now - timedelta(days=30)
    ).all()
    for item in rows:
        remind = item.remind_at
        created_at = item.created_at
        if remind is not None:
            if remind.tzinfo is None:
                remind = remind.replace(tzinfo=timezone.utc)
            if remind < now or remind > soon:
                continue
        else:
            if created_at is None:
                continue
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if created_at < now - timedelta(hours=24):
                continue
        key = f"visit:{item.user_id}:appt:{item.id}"
        if enqueue_mission(
            "visit_pack",
            item.user_id,
            payload={"message": item.reason or item.specialty, "appointment_id": item.id},
            dedupe_key=key,
        ):
            created += 1
    return created


def queued_weekly_digests() -> int:
    from missions.enqueue import enqueue_mission

    today = datetime.now(timezone.utc)
    if today.weekday() != 6 and not _force_digest():
        return 0
    week = today.strftime("%Y-%W")
    created = 0
    from models import AppointmentRequest, LabResult, UserMedication

    for user in User.query.all():
        active = (
            UserMedication.query.filter_by(user_id=user.id).first()
            or LabResult.query.filter_by(user_id=user.id).first()
            or AppointmentRequest.query.filter_by(user_id=user.id).first()
        )
        if not active:
            continue
        row = enqueue_mission(
            "digest",
            user.id,
            payload={},
            dedupe_key=f"digest:{user.id}:{week}",
        )
        if row is not None:
            created += 1
    return created


def _force_digest() -> bool:
    import os

    return os.getenv("BLOOM_FORCE_DIGEST") == "1"


def _load(path: str):
    module_name, func_name = path.split(":")
    module = __import__(module_name, fromlist=[func_name])
    return getattr(module, func_name)
