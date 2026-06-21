"""
Authentication module for CortexCart.

- Signup / Login / Logout
- bcrypt-hashed passwords
- JWT-based session tokens
- Role-based access decorators (require_auth, require_admin)
- Supabase backend when configured, with a local JSON file fallback so the
  feature works out-of-the-box for development.
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Optional

import bcrypt
import jwt
from flask import Blueprint, current_app, g, jsonify, request

from supabase_client import get_supabase, is_supabase_configured

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# ── Config ────────────────────────────────────────────────────────────
JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production-please")
JWT_ALG = "HS256"
JWT_TTL_HOURS = int(os.environ.get("JWT_TTL_HOURS", "24"))

# Bootstrap a default admin in dev if env vars are set.
DEFAULT_ADMIN_USERNAME = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD")  # only seeded if set

# Local JSON store for fallback mode.
_LOCAL_STORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".local_users.json")

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ── Local store helpers (fallback when Supabase not configured) ──────
def _load_local() -> dict:
    if not os.path.exists(_LOCAL_STORE):
        return {"users": []}
    try:
        with open(_LOCAL_STORE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"users": []}


def _save_local(data: dict) -> None:
    try:
        with open(_LOCAL_STORE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️  Failed to persist local users: {e}")


# ── Password helpers ──────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ── User repository (Supabase or local) ──────────────────────────────
def find_user(username: str) -> Optional[dict]:
    username = (username or "").strip().lower()
    if not username:
        return None
    if is_supabase_configured():
        client = get_supabase()
        try:
            res = (
                client.table("app_users")
                .select("*")
                .eq("username", username)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            print(f"⚠️  Supabase find_user failed, using local: {e}")
    data = _load_local()
    for u in data.get("users", []):
        if u.get("username") == username:
            return u
    return None


def find_user_by_id(user_id: str) -> Optional[dict]:
    if is_supabase_configured():
        client = get_supabase()
        try:
            res = client.table("app_users").select("*").eq("id", user_id).limit(1).execute()
            return res.data[0] if res.data else None
        except Exception:
            pass
    data = _load_local()
    for u in data.get("users", []):
        if u.get("id") == user_id:
            return u
    return None


def insert_user(username: str, email: str, password_hash: str, role: str = "user", full_name: str = "") -> dict:
    record = {
        "id": str(uuid.uuid4()),
        "username": username.lower(),
        "email": (email or "").lower() or None,
        "password_hash": password_hash,
        "role": role,
        "is_active": True,
        "full_name": full_name or None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if is_supabase_configured():
        client = get_supabase()
        try:
            res = client.table("app_users").insert(record).execute()
            return res.data[0] if res.data else record
        except Exception as e:
            print(f"⚠️  Supabase insert_user failed, using local: {e}")
    data = _load_local()
    data.setdefault("users", []).append(record)
    _save_local(data)
    return record


def update_last_login(user_id: str):
    now = datetime.now(timezone.utc).isoformat()
    if is_supabase_configured():
        client = get_supabase()
        try:
            client.table("app_users").update({"last_login_at": now}).eq("id", user_id).execute()
            return
        except Exception:
            pass
    data = _load_local()
    for u in data.get("users", []):
        if u.get("id") == user_id:
            u["last_login_at"] = now
            _save_local(data)
            return


def list_users(limit: int = 200) -> list[dict]:
    if is_supabase_configured():
        client = get_supabase()
        try:
            res = (
                client.table("app_users")
                .select("id, username, email, role, is_active, full_name, last_login_at, created_at")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return res.data or []
        except Exception:
            pass
    data = _load_local()
    safe = []
    for u in data.get("users", [])[-limit:]:
        safe.append({k: v for k, v in u.items() if k != "password_hash"})
    return list(reversed(safe))


def update_user_admin(user_id: str, *, role: Optional[str] = None, is_active: Optional[bool] = None) -> Optional[dict]:
    patch: dict = {}
    if role in ("user", "admin"):
        patch["role"] = role
    if isinstance(is_active, bool):
        patch["is_active"] = is_active
    if not patch:
        return find_user_by_id(user_id)
    if is_supabase_configured():
        client = get_supabase()
        try:
            res = client.table("app_users").update(patch).eq("id", user_id).execute()
            return res.data[0] if res.data else None
        except Exception:
            pass
    data = _load_local()
    for u in data.get("users", []):
        if u.get("id") == user_id:
            u.update(patch)
            _save_local(data)
            return u
    return None


def log_auth_event(event: str, user_id: Optional[str], username: Optional[str]):
    rec = {
        "user_id": user_id,
        "username": (username or "").lower() or None,
        "event": event,
        "ip_address": (request.headers.get("X-Forwarded-For") or request.remote_addr or "")[:64] if request else None,
        "user_agent": (request.headers.get("User-Agent") or "")[:255] if request else None,
    }
    if is_supabase_configured():
        client = get_supabase()
        try:
            client.table("auth_events").insert(rec).execute()
        except Exception as e:
            print(f"⚠️  Supabase log_auth_event failed: {e}")


# ── JWT helpers ───────────────────────────────────────────────────────
def issue_token(user: dict) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["id"],
        "username": user["username"],
        "role": user.get("role", "user"),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=JWT_TTL_HOURS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError:
        return None


def _get_token_from_request() -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(None, 1)[1].strip()
    # Fallback: cookie
    return request.cookies.get("cortexcart_token")


def get_current_user() -> Optional[dict]:
    token = _get_token_from_request()
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user = find_user_by_id(payload.get("sub", ""))
    if not user or not user.get("is_active", True):
        return None
    return user


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        if user.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper


def _safe_user(u: dict) -> dict:
    return {
        "id": u.get("id"),
        "username": u.get("username"),
        "email": u.get("email"),
        "role": u.get("role", "user"),
        "full_name": u.get("full_name"),
        "is_active": u.get("is_active", True),
        "last_login_at": u.get("last_login_at"),
        "created_at": u.get("created_at"),
    }


# ── Bootstrap default admin (dev convenience) ─────────────────────────
def bootstrap_default_admin():
    if not DEFAULT_ADMIN_PASSWORD:
        return
    existing = find_user(DEFAULT_ADMIN_USERNAME)
    if existing:
        return
    insert_user(
        username=DEFAULT_ADMIN_USERNAME,
        email=os.environ.get("DEFAULT_ADMIN_EMAIL", f"{DEFAULT_ADMIN_USERNAME}@cortexcart.local"),
        password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
        role="admin",
        full_name="CortexCart Administrator",
    )
    print(f"✅  Bootstrapped default admin '{DEFAULT_ADMIN_USERNAME}'.")


# ── Routes ────────────────────────────────────────────────────────────
@auth_bp.route("/signup", methods=["POST"])
def signup():
    body = request.get_json(silent=True) or {}
    username = (body.get("username") or "").strip().lower()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    full_name = (body.get("full_name") or "").strip()

    if not USERNAME_RE.match(username):
        return jsonify({"error": "Username must be 3-32 chars (letters, numbers, _ . -)"}), 400
    if email and not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email address"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if find_user(username):
        return jsonify({"error": "Username already exists"}), 409

    user = insert_user(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role="user",
        full_name=full_name,
    )
    log_auth_event("signup", user["id"], username)
    token = issue_token(user)
    return jsonify({"user": _safe_user(user), "token": token}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    username = (body.get("username") or "").strip().lower()
    password = body.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = find_user(username)
    if not user or not verify_password(password, user.get("password_hash", "")):
        log_auth_event("login_failed", user["id"] if user else None, username)
        # Constant-ish delay to slow down brute force
        time.sleep(0.3)
        return jsonify({"error": "Invalid username or password"}), 401
    if not user.get("is_active", True):
        return jsonify({"error": "Account is disabled"}), 403

    update_last_login(user["id"])
    log_auth_event("login", user["id"], username)
    token = issue_token(user)
    return jsonify({"user": _safe_user(user), "token": token})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    user = get_current_user()
    if user:
        log_auth_event("logout", user["id"], user.get("username"))
    return jsonify({"ok": True})


@auth_bp.route("/me", methods=["GET"])
def me():
    user = get_current_user()
    if not user:
        return jsonify({"user": None}), 200
    return jsonify({"user": _safe_user(user)})
