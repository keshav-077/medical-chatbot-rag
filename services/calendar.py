"""Optional Google Calendar read access for suggested visit times."""

import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import requests

SCOPES = "https://www.googleapis.com/auth/calendar.readonly"


def oauth_configured() -> bool:
    return bool(os.getenv("GOOGLE_OAUTH_CLIENT_ID") and os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"))


def auth_url(redirect_uri: str, state: str) -> str:
    query = urlencode(
        {
            "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


def exchange_code(code: str, redirect_uri: str) -> dict:
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def _access_token(refresh_token: str) -> str:
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def suggest_slots(refresh_token: str | None, count: int = 3) -> list[str]:
    """Return ISO times. Without a calendar token, suggest weekday mornings in IST."""
    now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    suggestions = []
    day = now + timedelta(days=1)
    while len(suggestions) < count:
        if day.weekday() < 5:
            slot = day.replace(hour=10, minute=0, second=0, microsecond=0)
            suggestions.append(slot.strftime("%Y-%m-%d %H:%M IST"))
        day += timedelta(days=1)
    if not refresh_token or not oauth_configured():
        return suggestions
    try:
        token = _access_token(refresh_token)
        start = datetime.now(timezone.utc)
        end = start + timedelta(days=7)
        response = requests.post(
            "https://www.googleapis.com/calendar/v3/freeBusy",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "timeMin": start.isoformat(),
                "timeMax": end.isoformat(),
                "items": [{"id": "primary"}],
            },
            timeout=20,
        )
        response.raise_for_status()
        busy = response.json().get("calendars", {}).get("primary", {}).get("busy", [])
        if not busy:
            return suggestions
        return suggestions + ["Calendar connected. Busy blocks were found; confirm the morning slot still works."]
    except requests.RequestException:
        return suggestions
