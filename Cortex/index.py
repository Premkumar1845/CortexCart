"""
Vercel serverless entry point.
Exposes the Flask app as a WSGI handler for Vercel's Python runtime.
"""
import sys
import os

# Ensure VERCEL env is set so the engine uses the right dataset/paths
os.environ.setdefault("VERCEL", "1")

# Add backend directory to Python path so Flask app can import its modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import app
