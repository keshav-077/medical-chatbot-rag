"""Local India safety notices. Same file the worker already scans."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_PATH = ROOT / "Data" / "medicines" / "safety_notices.json"
# worker/jobs.py historically used data/medicines (lowercase)
_ALT = ROOT / "data" / "medicines" / "safety_notices.json"


def list_safety_notices(drug: str = "") -> list[dict]:
    path = _PATH if _PATH.exists() else _ALT
    if not path.exists():
        return []
    try:
        notices = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    needle = (drug or "").lower().strip()
    if not needle:
        return notices
    return [row for row in notices if needle in (row.get("drug") or "").lower()]
