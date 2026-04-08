"""
AI Explanation Layer – "Why this product?" powered by LLM
"""

import os
import requests as http_requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def explain_recommendation(product: dict, context: str, user_query: str = "") -> str:
    """
    Generate a short, persuasive explanation of why a product is recommended.
    Returns a plain-text explanation (2-3 sentences).
    """
    if not OPENROUTER_API_KEY:
        return _fallback_explanation(product, context)

    prompt = f"""You are a concise shopping assistant. Explain in 2-3 short sentences why this product is recommended.

Context: {context}
{f'User was looking for: {user_query}' if user_query else ''}

Product: {product.get('name', '')}
Brand: {product.get('brandName', '')}
Price: ${product.get('finalPrice', 0):,.0f} (retail ${product.get('retailPrice', 0):,.0f})
Category: {product.get('department', '')}
Similarity: {product.get('similarity_score', 0):.0%}
Rating: {product.get('rating', 'N/A')}/5

Be specific about why it's a good match. Mention price, features, or brand as relevant. Do NOT use bullet points."""

    try:
        resp = http_requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
                "temperature": 0.6,
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return _fallback_explanation(product, context)


def explain_batch(products: list[dict], context: str, user_query: str = "") -> list[dict]:
    """Add 'explanation' field to top products (max 5 to limit API calls)."""
    for p in products[:5]:
        p["explanation"] = explain_recommendation(p, context, user_query)
    return products


def _fallback_explanation(product: dict, context: str) -> str:
    """Rule-based explanation when LLM is unavailable."""
    parts = []

    sim = product.get("similarity_score", 0)
    if sim > 0.7:
        parts.append(f"Highly similar match ({sim:.0%} similarity)")
    elif sim > 0.4:
        parts.append(f"Good match based on product features ({sim:.0%} similarity)")

    discount = product.get("discount_pct", 0)
    if discount > 20:
        parts.append(f"Currently {discount:.0f}% off retail price")

    rating = product.get("rating", 0)
    if rating >= 4.5:
        parts.append(f"Top-rated at {rating}/5 stars")

    brand = product.get("brandName", "")
    if brand and brand != "Unknown":
        parts.append(f"From trusted brand {brand}")

    if not parts:
        parts.append("Recommended based on content similarity analysis")

    return ". ".join(parts) + "."
