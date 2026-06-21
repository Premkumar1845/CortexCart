"""
Admin module – user management, product moderation, and ops endpoints.
All routes require an authenticated admin user.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading

from flask import Blueprint, current_app, jsonify, request

from auth import (
    list_users,
    require_admin,
    update_user_admin,
)
from supabase_client import get_supabase, is_supabase_configured

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ── Users ─────────────────────────────────────────────────────────────
@admin_bp.route("/users", methods=["GET"])
@require_admin
def list_all_users():
    return jsonify({"users": list_users(limit=int(request.args.get("limit", 200)))})


@admin_bp.route("/users/<user_id>", methods=["PATCH"])
@require_admin
def update_user(user_id: str):
    body = request.get_json(silent=True) or {}
    role = body.get("role")
    is_active = body.get("is_active")
    updated = update_user_admin(user_id, role=role, is_active=is_active)
    if not updated:
        return jsonify({"error": "User not found"}), 404
    safe = {k: v for k, v in updated.items() if k != "password_hash"}
    return jsonify({"user": safe})


# ── Products (CRUD) ───────────────────────────────────────────────────
@admin_bp.route("/products/<product_id>", methods=["DELETE"])
@require_admin
def delete_product(product_id: str):
    """Delete a product from the in-memory engine and from Supabase if present."""
    engine = current_app.config.get("RECOMMENDATION_ENGINE")
    deleted_engine = False
    if engine is not None and hasattr(engine, "delete_product"):
        try:
            deleted_engine = bool(engine.delete_product(product_id))
        except Exception as e:
            print(f"⚠️  engine.delete_product failed: {e}")

    deleted_db = False
    if is_supabase_configured():
        client = get_supabase()
        try:
            client.table("products").delete().eq("id", product_id).execute()
            deleted_db = True
        except Exception as e:
            print(f"⚠️  Supabase product delete failed: {e}")

    if not (deleted_engine or deleted_db):
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"deleted": True, "engine": deleted_engine, "db": deleted_db})


@admin_bp.route("/products/<product_id>", methods=["PATCH"])
@require_admin
def update_product(product_id: str):
    body = request.get_json(silent=True) or {}
    if not body:
        return jsonify({"error": "No fields provided"}), 400
    updated_db = False
    if is_supabase_configured():
        client = get_supabase()
        try:
            res = client.table("products").update(body).eq("id", product_id).execute()
            updated_db = bool(res.data)
        except Exception as e:
            return jsonify({"error": f"DB update failed: {e}"}), 500
    return jsonify({"updated": True, "db": updated_db})


# ── Re-seed embeddings (background job) ───────────────────────────────
_reseed_state = {"running": False, "started_at": None, "exit_code": None, "log_tail": ""}


def _run_reseed():
    global _reseed_state
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script = os.path.join(project_root, "scripts", "seed_embeddings.py")
    if not os.path.isfile(script):
        _reseed_state.update({"running": False, "exit_code": -1, "log_tail": "seed_embeddings.py not found"})
        return
    try:
        proc = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            timeout=60 * 30,
        )
        tail = (proc.stdout + "\n" + proc.stderr)[-2000:]
        _reseed_state.update({
            "running": False,
            "exit_code": proc.returncode,
            "log_tail": tail,
        })
    except Exception as e:
        _reseed_state.update({"running": False, "exit_code": -1, "log_tail": str(e)})


@admin_bp.route("/reseed", methods=["POST"])
@require_admin
def reseed_embeddings():
    from datetime import datetime, timezone
    if _reseed_state["running"]:
        return jsonify({"error": "A reseed job is already running"}), 409
    _reseed_state.update({
        "running": True,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "exit_code": None,
        "log_tail": "",
    })
    threading.Thread(target=_run_reseed, daemon=True).start()
    return jsonify({"started": True})


@admin_bp.route("/reseed/status", methods=["GET"])
@require_admin
def reseed_status():
    return jsonify(_reseed_state)
