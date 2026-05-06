"""
Flask API – CortexCart AI Decision Engine for Shopping
Multi-modal recommendations with vector similarity, hybrid ranking,
AI explanations, and user behavior tracking.
"""

import io
import json
import os
import traceback

import numpy as np
import pandas as pd
import requests as http_requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from recommendation_engine import RecommendationEngine
from hybrid_ranking import hybrid_rank, categorize_recommendations
from ai_explainer import explain_recommendation, explain_batch, _fallback_explanation
from behavior_tracker import track_activity, get_user_history, get_viewed_product_ids, generate_session_id

# ── Load .env ─────────────────────────────────────────────────────────
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

# ── Static build path (React production build) ───────────────────────
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_BACKEND_DIR)
STATIC_DIR = os.path.join(_PROJECT_DIR, "frontend", "dist")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
CORS(app)

# ── Bootstrap engine (lazy on Vercel, eager locally) ──────────────────
engine = RecommendationEngine()
_engine_ready = False
_IS_VERCEL = bool(os.environ.get("VERCEL"))

# Optional: vector engine for semantic search (requires sentence-transformers)
_vector_engine = None
_vector_ready = False


def _ensure_engine():
    global _engine_ready
    if not _engine_ready:
        print("⏳  Building recommendation engine …")
        engine.build()
        print("✅  Engine ready.")
        _engine_ready = True


def _get_vector_engine():
    """Lazy-load vector engine (optional – gracefully degrades)."""
    global _vector_engine, _vector_ready
    if _vector_ready:
        return _vector_engine
    _vector_ready = True
    try:
        from vector_engine import vector_engine
        _vector_engine = vector_engine
        print("✅  Vector engine loaded.")
    except ImportError:
        print("⚠️  Vector engine not available (sentence-transformers not installed). Using TF-IDF fallback.")
        _vector_engine = None
    return _vector_engine


# Build immediately when running locally (not on Vercel)
if not _IS_VERCEL:
    _ensure_engine()


# ── Health ────────────────────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    vec = _get_vector_engine()
    return jsonify({
        "status": "ok",
        "engine": "ready" if _engine_ready else "not_ready",
        "vector_search": "available" if vec else "fallback_tfidf",
    })


# ── Product catalog (paginated, searchable) ───────────────────────────
@app.route("/api/products", methods=["GET"])
def get_products():
    _ensure_engine()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", None, type=str)
    per_page = min(per_page, 100)  # cap
    data = engine.get_products(page=page, per_page=per_page, search=search)
    return jsonify(data)


# ── Single product detail ─────────────────────────────────────────────
@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    _ensure_engine()
    product = engine.get_product_by_index(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)


# ── Real-time recommendation (enhanced with hybrid ranking) ───────────
@app.route("/api/recommend/realtime", methods=["POST"])
def recommend_realtime():
    _ensure_engine()
    body = request.get_json(silent=True) or {}
    product_id = body.get("product_id")
    query = body.get("query")
    brand = body.get("brand")
    top_n = min(body.get("top_n", 10), 50)

    if product_id is not None:
        try:
            recs = engine.recommend_by_index(int(product_id), top_n=top_n)
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    elif query:
        recs = engine.recommend_by_query(query, brand=brand, top_n=top_n)
    else:
        return jsonify({"error": "Provide 'product_id' or 'query'"}), 400

    # Apply hybrid ranking
    source_product = None
    if product_id is not None:
        source_product = engine.get_product_by_index(int(product_id))
    recs = hybrid_rank(recs, boost_brand=brand)

    return jsonify({"recommendations": recs})


# ── Smart Recommendations (vector + hybrid + categorized) ─────────────
@app.route("/api/recommend/smart", methods=["POST"])
def recommend_smart():
    """
    Enhanced recommendation with categorized sections:
    best_for_you, similar_products, budget_picks, premium_picks, best_value
    """
    _ensure_engine()
    body = request.get_json(silent=True) or {}
    product_id = body.get("product_id")
    query = body.get("query")
    brand = body.get("brand")
    session_id = body.get("session_id")
    top_n = min(body.get("top_n", 20), 50)

    source_product = None

    # Get recommendations
    if product_id is not None:
        try:
            recs = engine.recommend_by_index(int(product_id), top_n=top_n)
            source_product = engine.get_product_by_index(int(product_id))
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        # Track view
        if session_id:
            track_activity(session_id, str(product_id), "click_similar")
    elif query:
        recs = engine.recommend_by_query(query, brand=brand, top_n=top_n)
        if session_id:
            track_activity(session_id, "", "search", {"query": query})
    else:
        return jsonify({"error": "Provide 'product_id' or 'query'"}), 400

    # Hybrid rank all results
    price_target = source_product.get("finalPrice") if source_product else None
    recs = hybrid_rank(recs, price_target=price_target, boost_brand=brand)

    # Categorize into sections
    sections = categorize_recommendations(recs, source_product)

    return jsonify({
        "source_product": source_product,
        "sections": sections,
        "total": len(recs),
    })


# ── Explain Recommendation ────────────────────────────────────────────
@app.route("/api/recommend/explain", methods=["POST"])
def explain_rec():
    """Generate an AI explanation for why a product is recommended."""
    body = request.get_json(silent=True) or {}
    product = body.get("product", {})
    context = body.get("context", "Similar product recommendation")
    user_query = body.get("user_query", "")

    if not product:
        return jsonify({"error": "Product data required"}), 400

    explanation = explain_recommendation(product, context, user_query)
    return jsonify({"explanation": explanation})


# ── User Behavior Tracking ────────────────────────────────────────────
@app.route("/api/track", methods=["POST"])
def track():
    """Track user activity (view, like, search, click_similar)."""
    body = request.get_json(silent=True) or {}
    session_id = body.get("session_id", "")
    product_id = body.get("product_id", "")
    action = body.get("action", "")
    metadata = body.get("metadata", {})

    if not session_id or not action:
        return jsonify({"error": "session_id and action required"}), 400

    track_activity(session_id, product_id, action, metadata)
    return jsonify({"status": "tracked"})


@app.route("/api/session", methods=["POST"])
def create_session():
    """Create a new anonymous session for behavior tracking."""
    sid = generate_session_id()
    return jsonify({"session_id": sid})


# ── Personalized Recommendations ──────────────────────────────────────
@app.route("/api/recommend/personalized", methods=["POST"])
def recommend_personalized():
    """Get recommendations based on user's browsing history."""
    _ensure_engine()
    body = request.get_json(silent=True) or {}
    session_id = body.get("session_id", "")
    top_n = min(body.get("top_n", 10), 30)

    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    viewed_ids = get_viewed_product_ids(session_id)
    if not viewed_ids:
        # No history → return popular/featured products
        data = engine.get_products(page=1, per_page=top_n)
        return jsonify({
            "recommendations": data.get("products", []),
            "personalized": False,
            "message": "No browsing history yet. Showing featured products.",
        })

    # Aggregate recommendations from viewed products
    all_recs = []
    seen_ids = set()
    for pid in viewed_ids[:5]:
        try:
            pid_int = int(pid) if isinstance(pid, str) and pid.isdigit() else None
            if pid_int is not None:
                recs = engine.recommend_by_index(pid_int, top_n=8)
                for r in recs:
                    rid = r.get("id")
                    if rid not in seen_ids and str(rid) not in viewed_ids:
                        seen_ids.add(rid)
                        all_recs.append(r)
        except Exception:
            continue

    # Hybrid rank the aggregated results
    ranked = hybrid_rank(all_recs)[:top_n]

    return jsonify({
        "recommendations": ranked,
        "personalized": True,
        "based_on": len(viewed_ids),
    })


# ── Batch recommendation (CSV upload) ─────────────────────────────────
@app.route("/api/recommend/batch", methods=["POST"])
def recommend_batch():
    _ensure_engine()
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files are accepted"}), 400

    try:
        queries_df = pd.read_csv(file.stream)
    except Exception:
        return jsonify({"error": "Could not parse CSV"}), 400

    top_n = request.form.get("top_n", 5, type=int)
    top_n = min(top_n, 20)
    results = engine.recommend_batch(queries_df, top_n=top_n)

    # Return as downloadable CSV or JSON
    fmt = request.form.get("format", "json")
    if fmt == "csv":
        out_df = pd.DataFrame(results)
        buf = io.BytesIO()
        out_df.to_csv(buf, index=False)
        buf.seek(0)
        return send_file(
            buf,
            mimetype="text/csv",
            as_attachment=True,
            download_name="recommendations.csv",
        )

    return jsonify({"recommendations": results, "total": len(results)})


# ── AI-powered recommendation (OpenRouter LLM with engine fallback) ──
import re

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Try free models in order – first one that responds wins.
OPENROUTER_MODELS = [
    m.strip() for m in os.environ.get(
        "OPENROUTER_MODELS",
        "mistralai/mistral-7b-instruct:free,"
        "google/gemma-2-9b-it:free,"
        "meta-llama/llama-3.2-3b-instruct:free,"
        "qwen/qwen-2-7b-instruct:free",
    ).split(",") if m.strip()
]


def _parse_budget(message: str):
    """Extract a max-price budget (USD) from natural language."""
    if not message:
        return None
    m = re.search(
        r"(?:under|below|less than|<=?|upto|up to|max(?:imum)?|within|cheaper than)"
        r"\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(k|K)?",
        message,
    )
    if not m:
        m = re.search(r"\$\s*([\d,]+(?:\.\d+)?)\s*(k|K)?", message)
    if not m:
        return None
    try:
        val = float(m.group(1).replace(",", ""))
        if m.group(2) and m.group(2).lower() == "k":
            val *= 1000
        return val
    except (ValueError, IndexError):
        return None


def _build_fallback_reply(user_message: str):
    """Generate a recommendation reply using the local engine (no LLM)."""
    budget = _parse_budget(user_message)
    # Strip price phrases so the text query focuses on the product itself
    cleaned = re.sub(
        r"(under|below|less than|<=?|upto|up to|max(?:imum)?|within|cheaper than)?"
        r"\s*\$?\s*[\d,]+(?:\.\d+)?\s*(k|K)?\s*(dollars|usd)?",
        " ",
        user_message,
        flags=re.IGNORECASE,
    ).strip() or user_message

    try:
        recs = engine.recommend_by_query(cleaned, top_n=30)
    except Exception:
        recs = []

    if budget is not None:
        recs = [
            r for r in recs
            if isinstance(r.get("finalPrice"), (int, float)) and 0 < r["finalPrice"] <= budget
        ]
    recs = recs[:5]

    if not recs:
        return (
            "I couldn't find products that match that description in our catalog. "
            "Try a different keyword (e.g. \"Rolex watches\", \"Gucci handbags\", "
            "\"sunglasses under $200\")."
        )

    lines = [f"Here are {len(recs)} picks from our catalog"]
    if budget is not None:
        lines[0] += f" under ${int(budget):,}"
    lines[0] += ":\n"
    for i, r in enumerate(recs, 1):
        price = r.get("finalPrice") or r.get("retailPrice") or "N/A"
        if isinstance(price, (int, float)):
            price = f"${price:,.2f}"
        lines.append(
            f"{i}. **{r.get('brandName', '')} — {r.get('name', '')}** ({price})\n"
            f"   _Why_: matches your query \"{cleaned}\" with similarity "
            f"{r.get('similarity_score', 0):.2f}."
        )
    return "\n".join(lines)


def _try_openrouter(user_message: str):
    """Call OpenRouter with model fallback. Returns reply string or None."""
    if not OPENROUTER_API_KEY:
        return None

    sample = engine.get_products(
        page=1, per_page=30,
        search=user_message.split()[0] if user_message else None,
    )
    product_context = ""
    for p in sample.get("products", [])[:15]:
        product_context += (
            f"- ID:{p['id']} | {p.get('brandName','')} {p.get('name','')} | "
            f"${p.get('finalPrice', 'N/A')} (retail ${p.get('retailPrice', 'N/A')}) | "
            f"{p.get('department', '')}\n"
        )

    system_prompt = (
        "You are CortexCart AI, a recommendation assistant for a luxury e-commerce "
        "store (watches, jewelry, handbags, sunglasses) with 94,000+ products.\n"
        "Recommend products from the catalog provided. Include brand, name, price, "
        "and a one-sentence reason. Use a numbered list. Be concise and friendly.\n\n"
        f"Catalog sample:\n{product_context}"
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.environ.get("APP_URL", "https://cortexcart.local"),
        "X-Title": "CortexCart",
    }
    payload_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    last_err = None
    for model in OPENROUTER_MODELS:
        try:
            resp = http_requests.post(
                OPENROUTER_URL,
                headers=headers,
                json={
                    "model": model,
                    "messages": payload_messages,
                    "max_tokens": 1024,
                    "temperature": 0.7,
                },
                timeout=25,
            )
            if resp.status_code >= 400:
                last_err = f"{model} → HTTP {resp.status_code}: {resp.text[:200]}"
                print(f"⚠️  OpenRouter {last_err}")
                continue
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (http_requests.exceptions.RequestException, KeyError, IndexError, ValueError) as e:
            last_err = f"{model} → {e}"
            print(f"⚠️  OpenRouter {last_err}")
            continue
    if last_err:
        print(f"❌  All OpenRouter models failed. Last error: {last_err}")
    return None


@app.route("/api/ai/recommend", methods=["POST"])
def ai_recommend():
    _ensure_engine()
    body = request.get_json(silent=True) or {}
    user_message = body.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Please provide a message"}), 400

    # Try LLM first; fall back to local engine so the chat is always useful.
    llm_reply = _try_openrouter(user_message)
    if llm_reply:
        return jsonify({"reply": llm_reply, "source": "llm"})

    try:
        fallback = _build_fallback_reply(user_message)
        return jsonify({"reply": fallback, "source": "engine"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Recommendation failed: {e}"}), 500


# ── Error handlers ────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(_):
    traceback.print_exc()
    return jsonify({"error": "Internal server error"}), 500


# ── Serve React SPA (catch-all) ───────────────────────────────────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    # If the requested file exists in the build folder, serve it
    full_path = os.path.join(STATIC_DIR, path)
    if path and os.path.isfile(full_path):
        return send_from_directory(STATIC_DIR, path)
    # Otherwise serve index.html (React Router handles client routes)
    index = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index):
        return send_from_directory(STATIC_DIR, "index.html")
    return jsonify({"status": "API is running. Frontend not built yet."}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
