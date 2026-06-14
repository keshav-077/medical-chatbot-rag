# wsgi.py — Vercel entry point
# This file only exists for deployment. Do not modify app.py.

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app

# Vercel needs the app object to be named 'app'
# This is already satisfied since Flask app is named 'app' in app.py
