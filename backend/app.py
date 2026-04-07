"""
Flask API – Multi-Modal Product Recommendation System
"""

import io
import json
import os
import traceback

import pandas as pd
import requests as http_requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from recommendation_engine import RecommendationEngine

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


def _ensure_engine():
    global _engine_ready
    if not _engine_ready:
        print("⏳  Building recommendation engine …")
        engine.build()
        print("✅  Engine ready.")
        _engine_ready = True


# Build immediately when running locally (not on Vercel)
if not _IS_VERCEL:
    _ensure_engine()


# ── Health ────────────────────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


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


# ── Real-time recommendation ──────────────────────────────────────────
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

    return jsonify({"recommendations": recs})


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


# ── AI-powered recommendation (OpenRouter LLM) ───────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


@app.route("/api/ai/recommend", methods=["POST"])
def ai_recommend():
    _ensure_engine()
    body = request.get_json(silent=True) or {}
    user_message = body.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Please provide a message"}), 400

    if not OPENROUTER_API_KEY:
        return jsonify({"error": "AI service not configured"}), 503

    # Fetch a sample of products for context
    sample = engine.get_products(page=1, per_page=30, search=user_message.split()[0] if user_message else None)
    product_context = ""
    for p in sample.get("products", [])[:15]:
        product_context += (
            f"- ID:{p['id']} | {p['brandName']} {p['name']} | "
            f"${p.get('finalPrice', 'N/A')} (retail ${p.get('retailPrice', 'N/A')}) | "
            f"{p.get('department', '')}\n"
        )

    system_prompt = (
        "You are CortexCart AI, an intelligent product recommendation assistant for a luxury e-commerce store "
        "(watches, jewelry, handbags, sunglasses, etc.) with 94,000+ products.\n\n"
        "Your job is to understand what the user is looking for and recommend products from our catalog.\n"
        "When recommending products, always include the product ID, brand, name, and price.\n"
        "Format your recommendations clearly with numbered lists.\n"
        "Be conversational, helpful, and concise.\n\n"
        f"Here are some relevant products from our catalog:\n{product_context}"
    )

    try:
        resp = http_requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": 1024,
                "temperature": 0.7,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        ai_reply = data["choices"][0]["message"]["content"]
        return jsonify({"reply": ai_reply})
    except http_requests.exceptions.Timeout:
        return jsonify({"error": "AI service timed out. Try again."}), 504
    except http_requests.exceptions.RequestException as e:
        return jsonify({"error": f"AI service error: {str(e)}"}), 502
    except (KeyError, IndexError):
        return jsonify({"error": "Unexpected AI response format"}), 502


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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
