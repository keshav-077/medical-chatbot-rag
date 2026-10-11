"""Background jobs: ingest, reminders, and medicine safety notices."""

import json
from datetime import datetime, timezone
from pathlib import Path

from models import AppointmentRequest, IngestJob, Notification, UserMedication, db
from ingestion.pipeline import run_ingest

ROOT = Path(__file__).resolve().parents[1]


def run_reminders() -> int:
    now = datetime.now(timezone.utc)
    due = (
        AppointmentRequest.query.filter(AppointmentRequest.reminded_at.is_(None))
        .filter(AppointmentRequest.remind_at.isnot(None))
        .filter(AppointmentRequest.remind_at <= now)
        .all()
    )
    for item in due:
        db.session.add(
            Notification(
                user_id=item.user_id,
                kind="appointment",
                message=(
                    f"Reminder: {item.specialty or 'clinic'} visit"
                    f"{' at ' + item.place_name if item.place_name else ''}. "
                    f"Reason: {item.reason[:180]}"
                ),
            )
        )
        item.reminded_at = now
    db.session.commit()
    return len(due)


def run_safety_notices() -> int:
    path = ROOT / "data" / "medicines" / "safety_notices.json"
    notices = json.loads(path.read_text(encoding="utf-8"))
    created = 0
    meds = UserMedication.query.all()
    for med in meds:
        name = med.name.lower()
        for notice in notices:
            drug = (notice.get("drug") or "").lower()
            if drug and drug in name:
                text = f"{notice.get('source')}: {notice.get('message')} ({notice.get('document_date')})"
                exists = Notification.query.filter_by(user_id=med.user_id, message=text).first()
                if exists:
                    continue
                db.session.add(
                    Notification(user_id=med.user_id, kind="safety", message=text)
                )
                created += 1
    db.session.add(
        IngestJob(
            source_id="safety_notices",
            status="ok",
            detail=f"created {created} notifications",
            ran_at=datetime.now(timezone.utc),
        )
    )
    db.session.commit()
    return created
