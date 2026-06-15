"""
Vercel serverless entry point.

This file is the WSGI handler that Vercel's Python runtime invokes.
It imports the Flask app (which is WSGI-compatible) and exposes it
as the 'app' variable that Vercel expects.

IMPORTANT: This file must NOT call app.run() — Vercel manages the server.
"""

import sys
import os

# Add project root to Python path so imports work correctly
# (Vercel runs from the api/ directory, but our modules are in the project root)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Force production environment on Vercel
os.environ.setdefault("FLASK_ENV", "production")

# Import the Flask app — Vercel expects a WSGI-compatible 'app' variable
from app import app  # noqa: E402

# Vercel's Python runtime will automatically use this 'app' variable
# to handle incoming HTTP requests. No app.run() needed.
