"""
Analytics module – aggregates metrics for the admin dashboard.

Queries Supabase when configured; otherwise falls back to local
in-memory tracker state (limited but works in dev).
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from auth import require_admin
from supabase_client import get_supabase, is_supabase_configured

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/admin/analytics")


def _safe_table_count(table: str) -> int:
    if not is_supabase_configured():
        return 0
    try:
        client = get_supabase()
        # Supabase python client: .select("id", count="exact")
        res = client.table(table).select("id", count="exact").limit(1).execute()
        return int(res.count or 0)
    except Exception:
        return 0


def _safe_table_count_filter(table: str, column: str, op: str, value) -> int:
    if not is_supabase_configured():
        return 0
    try:
        client = get_supabase()
        q = client.table(table).select("id", count="exact").limit(1)
        if op == "gte":
            q = q.gte(column, value)
        elif op == "eq":
            q = q.eq(column, value)
        res = q.execute()
        return int(res.count or 0)
    except Exception:
        return 0


@analytics_bp.route("/overview", methods=["GET"])
@require_admin
def overview():
    since_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    since_7d = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    data = {
        "users_total": _safe_table_count("app_users"),
        "users_active_7d": _safe_table_count_filter("auth_events", "created_at", "gte", since_7d),
        "logins_24h": _safe_table_count_filter("auth_events", "created_at", "gte", since_24h),
        "signups_7d": _safe_table_count_filter("app_users", "created_at", "gte", since_7d),
        "product_views_24h": 0,
        "searches_24h": 0,
        "recommendations_24h": _safe_table_count_filter(
            "recommendation_logs", "created_at", "gte", since_24h
        ),
        "rec_clicks_24h": _safe_table_count_filter(
            "recommendation_clicks", "created_at", "gte", since_24h
        ),
    }

    if is_supabase_configured():
        client = get_supabase()
        try:
            res = (
                client.table("user_activity")
                .select("id", count="exact")
                .eq("action", "view")
                .gte("created_at", since_24h)
                .limit(1)
                .execute()
            )
            data["product_views_24h"] = int(res.count or 0)
        except Exception:
            pass
        try:
            res = (
                client.table("user_activity")
                .select("id", count="exact")
                .eq("action", "search")
                .gte("created_at", since_24h)
                .limit(1)
                .execute()
            )
            data["searches_24h"] = int(res.count or 0)
        except Exception:
            pass

    # Click-through rate
    recs = data["recommendations_24h"] or 0
    clicks = data["rec_clicks_24h"] or 0
    data["ctr_24h"] = round((clicks / recs * 100), 2) if recs else 0.0

    return jsonify(data)


@analytics_bp.route("/signups", methods=["GET"])
@require_admin
def signups_timeseries():
    days = min(int(request.args.get("days", 30)), 180)
    if is_supabase_configured():
        client = get_supabase()
        try:
            res = client.rpc("analytics_daily_signups", {"days": days}).execute()
            return jsonify({"data": res.data or []})
        except Exception as e:
            return jsonify({"data": [], "warning": f"rpc failed: {e}"})
    return jsonify({"data": []})


@analytics_bp.route("/activity", methods=["GET"])
@require_admin
def activity_timeseries():
    days = min(int(request.args.get("days", 30)), 180)
    if is_supabase_configured():
        client = get_supabase()
        try:
            res = client.rpc("analytics_daily_activity", {"days": days}).execute()
            return jsonify({"data": res.data or []})
        except Exception as e:
            return jsonify({"data": [], "warning": f"rpc failed: {e}"})
    return jsonify({"data": []})


@analytics_bp.route("/top-products", methods=["GET"])
@require_admin
def top_products():
    limit = min(int(request.args.get("limit", 10)), 50)
    if is_supabase_configured():
        client = get_supabase()
        try:
            res = client.rpc("analytics_top_products", {"limit_n": limit}).execute()
            return jsonify({"data": res.data or []})
        except Exception as e:
            return jsonify({"data": [], "warning": f"rpc failed: {e}"})
    return jsonify({"data": []})


@analytics_bp.route("/searches", methods=["GET"])
@require_admin
def recent_searches():
    limit = min(int(request.args.get("limit", 50)), 200)
    if is_supabase_configured():
        client = get_supabase()
        try:
            res = (
                client.table("search_logs")
                .select("query, result_count, session_id, created_at")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            data = res.data or []
            top = Counter([(r.get("query") or "").lower() for r in data]).most_common(15)
            return jsonify({"recent": data, "top_queries": [{"query": q, "count": c} for q, c in top]})
        except Exception as e:
            return jsonify({"recent": [], "top_queries": [], "warning": str(e)})
    return jsonify({"recent": [], "top_queries": []})


@analytics_bp.route("/recommendations", methods=["GET"])
@require_admin
def rec_logs():
    limit = min(int(request.args.get("limit", 100)), 500)
    if is_supabase_configured():
        client = get_supabase()
        try:
            res = (
                client.table("recommendation_logs")
                .select("source, query, result_count, session_id, created_at")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            data = res.data or []
            by_source = Counter([r.get("source") for r in data])
            return jsonify({
                "recent": data,
                "by_source": [{"source": s, "count": c} for s, c in by_source.items()],
            })
        except Exception as e:
            return jsonify({"recent": [], "by_source": [], "warning": str(e)})
    return jsonify({"recent": [], "by_source": []})
