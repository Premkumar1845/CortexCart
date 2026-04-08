"""
Supabase Client Singleton
"""

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

_client = None


def get_supabase():
    """Return a cached Supabase client, or None if not configured."""
    global _client
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    if _client is None:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def is_supabase_configured():
    return bool(SUPABASE_URL and SUPABASE_KEY)
