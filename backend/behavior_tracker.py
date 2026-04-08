"""
User Behavior Tracking – anonymous session-based activity logging
"""

import uuid
from supabase_client import get_supabase, is_supabase_configured

# In-memory fallback when Supabase is not configured
_local_activity: dict[str, list[dict]] = {}


def track_activity(session_id: str, product_id: str, action: str, metadata: dict | None = None):
    """Record a user action (view, like, search, click_similar)."""
    if action not in ("view", "like", "search", "click_similar"):
        return

    if is_supabase_configured():
        client = get_supabase()
        client.table("user_activity").insert({
            "session_id": session_id,
            "product_id": product_id if action != "search" else None,
            "action": action,
            "metadata": metadata or {},
        }).execute()
    else:
        # Local fallback
        if session_id not in _local_activity:
            _local_activity[session_id] = []
        _local_activity[session_id].append({
            "product_id": product_id,
            "action": action,
            "metadata": metadata or {},
        })


def get_user_history(session_id: str, limit: int = 20) -> list[dict]:
    """Get recent product interactions for a session."""
    if is_supabase_configured():
        client = get_supabase()
        result = client.table("user_activity").select(
            "product_id, action, metadata, created_at"
        ).eq(
            "session_id", session_id
        ).order(
            "created_at", desc=True
        ).limit(limit).execute()
        return result.data
    else:
        return _local_activity.get(session_id, [])[-limit:]


def get_viewed_product_ids(session_id: str, limit: int = 20) -> list[str]:
    """Get product IDs that the user has viewed or liked."""
    history = get_user_history(session_id, limit)
    seen = []
    for item in history:
        pid = item.get("product_id")
        if pid and item.get("action") in ("view", "like") and pid not in seen:
            seen.append(pid)
    return seen


def generate_session_id() -> str:
    """Generate a new anonymous session ID."""
    return str(uuid.uuid4())
