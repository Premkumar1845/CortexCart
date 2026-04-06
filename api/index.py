"""
Vercel serverless entry point.
Exposes the Flask app as a WSGI handler for Vercel's Python runtime.
"""
import sys
import os

# Add backend directory to Python path so Flask app can import its modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import app
