"""
Environment-based configuration for Medical Chatbot RAG.

Usage:
    from config import get_config
    app.config.from_object(get_config())

Environments:
    - development: SQLite, debug mode, HTTP cookies
    - production: Neon PostgreSQL, no debug, HTTPS cookies, NullPool
"""

import os
import logging

logger = logging.getLogger(__name__)


def _get_database_url() -> str:
    """
    Get and normalize the database URL.

    Handles:
    - Neon/Heroku's postgres:// → postgresql:// conversion
    - Ensuring sslmode=require for Neon connections
    - Fallback to SQLite for local development
    """
    url = os.environ.get("DATABASE_URL")

    if not url:
        logger.warning(
            "DATABASE_URL not set — using SQLite (not suitable for production/serverless)"
        )
        return "sqlite:///medical_chatbot.db"

    # Neon and Heroku use 'postgres://' but SQLAlchemy requires 'postgresql://'
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # Neon requires SSL
    if "neon.tech" in url and "sslmode" not in url:
        separator = "&" if "?" in url else "?"
        url += f"{separator}sslmode=require"

    return url


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Rate limiting
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")


class DevelopmentConfig(Config):
    """Development configuration — local SQLite, debug mode."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _get_database_url()
    SESSION_COOKIE_SECURE = False  # Allow HTTP in dev


class ProductionConfig(Config):
    """
    Production configuration — Neon PostgreSQL, no debug.

    Uses NullPool because:
    - Vercel serverless functions are stateless (no persistent connections)
    - Neon provides its own PgBouncer connection pooler
    - Using SQLAlchemy's internal pool on top of Neon's pooler causes conflicts
    """

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _get_database_url()
    SESSION_COOKIE_SECURE = True  # HTTPS only in production

    # Engine options for PostgreSQL (NullPool for serverless)
    # Computed at class-load time since Flask's from_object() doesn't resolve @property
    _db_uri = _get_database_url()
    if _db_uri and _db_uri.startswith("postgresql"):
        from sqlalchemy.pool import NullPool
        SQLALCHEMY_ENGINE_OPTIONS = {
            "poolclass": NullPool,      # Let Neon's PgBouncer handle pooling
            "pool_pre_ping": True,      # Verify connections before use
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {}


# Configuration registry
_configs = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config():
    """
    Get the appropriate configuration based on FLASK_ENV.
    Defaults to 'development' if FLASK_ENV is not set.
    """
    env = os.environ.get("FLASK_ENV", "development").lower()
    config_class = _configs.get(env, DevelopmentConfig)
    logger.info(f"Using {env} configuration ({config_class.__name__})")
    return config_class()
