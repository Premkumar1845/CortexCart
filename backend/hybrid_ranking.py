"""
Hybrid Ranking Engine
Combines similarity, rating, and price signals for intelligent product ranking.
"""
from __future__ import annotations


def hybrid_rank(products: list[dict], price_target: float | None = None, boost_brand: str | None = None) -> list[dict]:
    """
    Re-rank products using weighted hybrid scoring:
      score = (0.55 * similarity) + (0.20 * rating_norm) + (0.15 * price_score) + (0.10 * discount_score)

    Optionally boost products matching a target price or brand.
    """
    if not products:
        return products

    # Extract values for normalization
    max_price = max((p.get("finalPrice", 0) for p in products), default=1) or 1
    max_rating = max((p.get("rating", 0) for p in products), default=5) or 5

    ranked = []
    for p in products:
        sim = p.get("similarity_score", 0)
        rating_norm = p.get("rating", 4.0) / max_rating
        discount_norm = min(p.get("discount_pct", 0) / 100, 1.0)

        # Price score: closer to target price = higher score, else inverse price
        if price_target and price_target > 0:
            price_diff = abs(p.get("finalPrice", 0) - price_target)
            price_score = max(0, 1 - (price_diff / max_price))
        else:
            # Default: favor mid-range (not too cheap, not too expensive)
            price_score = 1 - abs(p.get("finalPrice", 0) / max_price - 0.5)

        # Brand boost
        brand_bonus = 0
        if boost_brand and p.get("brandName", "").lower() == boost_brand.lower():
            brand_bonus = 0.1

        score = (
            0.55 * sim
            + 0.20 * rating_norm
            + 0.15 * price_score
            + 0.10 * discount_norm
            + brand_bonus
        )

        ranked.append({**p, "hybrid_score": round(score, 4)})

    ranked.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return ranked


def categorize_recommendations(products: list[dict], source_product: dict | None = None) -> dict:
    """
    Split ranked products into recommendation sections:
      - best_for_you: top hybrid-scored items
      - similar_products: highest similarity
      - budget_picks: cheapest with decent score
      - premium_picks: higher-end alternatives
      - best_value: highest discount with good score
    """
    if not products:
        return {
            "best_for_you": [],
            "similar_products": [],
            "budget_picks": [],
            "premium_picks": [],
            "best_value": [],
        }

    # Sort by hybrid score
    by_score = sorted(products, key=lambda x: x.get("hybrid_score", 0), reverse=True)
    # Sort by similarity
    by_sim = sorted(products, key=lambda x: x.get("similarity_score", 0), reverse=True)
    # Sort by price ascending
    by_price = sorted(products, key=lambda x: x.get("finalPrice", 0))
    # Sort by price descending
    by_price_desc = sorted(products, key=lambda x: x.get("finalPrice", 0), reverse=True)
    # Sort by discount
    by_discount = sorted(products, key=lambda x: x.get("discount_pct", 0), reverse=True)

    # Determine source price for budget/premium split
    source_price = source_product.get("finalPrice", 0) if source_product else 0
    if source_price > 0:
        budget = [p for p in by_price if p.get("finalPrice", 0) < source_price * 0.7]
        premium = [p for p in by_price_desc if p.get("finalPrice", 0) > source_price * 1.3]
    else:
        median_price = by_price[len(by_price) // 2].get("finalPrice", 0) if by_price else 0
        budget = [p for p in by_price if p.get("finalPrice", 0) < median_price * 0.6]
        premium = [p for p in by_price_desc if p.get("finalPrice", 0) > median_price * 1.5]

    return {
        "best_for_you": by_score[:5],
        "similar_products": by_sim[:6],
        "budget_picks": budget[:4],
        "premium_picks": premium[:4],
        "best_value": [p for p in by_discount if p.get("discount_pct", 0) > 10][:4],
    }
