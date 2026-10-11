# Production entry point for AWS (gunicorn) and any WSGI host.
# Local development still uses: python app.py

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app  # noqa: E402


def _require_production_env():
    if os.environ.get("FLASK_ENV", "development").lower() != "production":
        return
    missing = []
    secret = os.environ.get("SECRET_KEY") or ""
    if not secret or secret.startswith("dev-") or "change-this" in secret:
        missing.append("SECRET_KEY")
    for name in ("DATABASE_URL", "PINECONE_API_KEY", "JINA_API_KEY"):
        if not os.environ.get(name):
            missing.append(name)
    if not os.environ.get("OPENROUTER_API_KEY") and not os.environ.get("GROQ_API_KEY"):
        missing.append("OPENROUTER_API_KEY or GROQ_API_KEY")
    if missing:
        raise RuntimeError(
            "Refusing to start in production. Set: " + ", ".join(missing)
        )


_require_production_env()
