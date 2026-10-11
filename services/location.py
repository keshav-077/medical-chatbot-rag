"""Persist the last known user coordinate for care map and AQI."""

from datetime import datetime, timezone

from models import UserHealthProfile, db


def save_user_location(user_id: int, lat: float, lng: float, commit: bool = True) -> UserHealthProfile:
    row = UserHealthProfile.query.filter_by(user_id=user_id).first()
    if row is None:
        row = UserHealthProfile(user_id=user_id, allergies="", conditions="", notes="")
        db.session.add(row)
    row.last_lat = float(lat)
    row.last_lng = float(lng)
    row.last_located_at = datetime.now(timezone.utc)
    row.updated_at = datetime.now(timezone.utc)
    if commit:
        db.session.commit()
    return row


def get_user_location(user_id: int | None) -> tuple[float, float] | None:
    if not user_id:
        return None
    row = UserHealthProfile.query.filter_by(user_id=user_id).first()
    if row is None or row.last_lat is None or row.last_lng is None:
        return None
    return float(row.last_lat), float(row.last_lng)
