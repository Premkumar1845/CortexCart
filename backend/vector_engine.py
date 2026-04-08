"""
Vector Recommendation Engine – Supabase pgvector powered
Falls back to local embeddings cache when Supabase is not configured.
"""

import os
import numpy as np
import joblib
from supabase_client import get_supabase, is_supabase_configured

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_BACKEND_DIR)
_CACHE_DIR = os.path.join(_PROJECT_DIR, "models_cache")


class VectorEngine:
    """Handles vector similarity search via Supabase pgvector or local fallback."""

    def __init__(self):
        self._model = None
        self._local_embeddings = None
        self._local_meta = None
        self._local_ready = False

    # ── Lazy-load sentence-transformer for query encoding ─────
    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def encode_query(self, text: str) -> list[float]:
        """Convert a text query into a 384-dim embedding vector."""
        model = self._get_model()
        vec = model.encode([text], normalize_embeddings=True)
        return vec[0].tolist()

    # ── Local fallback ────────────────────────────────────────
    def _load_local_cache(self):
        if self._local_ready:
            return
        emb_path = os.path.join(_CACHE_DIR, "embeddings.npy")
        meta_path = os.path.join(_CACHE_DIR, "product_meta.pkl")
        if os.path.exists(emb_path) and os.path.exists(meta_path):
            self._local_embeddings = np.load(emb_path)
            self._local_meta = joblib.load(meta_path)
            self._local_ready = True

    def _local_search(self, query_vec: np.ndarray, top_n: int = 10, exclude_id: int | None = None):
        """Cosine similarity search over cached embeddings."""
        self._load_local_cache()
        if self._local_embeddings is None:
            return []

        # Cosine similarity (embeddings are normalized)
        scores = self._local_embeddings @ query_vec
        if exclude_id is not None and 0 <= exclude_id < len(scores):
            scores[exclude_id] = -1

        top_idx = np.argsort(scores)[::-1][:top_n]
        results = []
        df = self._local_meta
        for i in top_idx:
            row = df.iloc[i]
            results.append({
                "id": int(i),
                "name": str(row.get("name", "")),
                "brandName": str(row.get("brandName", "")),
                "product_type": str(row.get("product_type", "")),
                "department": str(row.get("department", "")),
                "description_short": str(row.get("description.short", "")),
                "finalPrice": float(row.get("pricing.finalPrice.value", 0)),
                "retailPrice": float(row.get("pricing.retailPrice.value", 0)),
                "discount_pct": round(float(row.get("discount_pct", 0)), 1),
                "rating": round(float(row.get("rating", 4.0)), 1) if "rating" in row.index else 4.0,
                "stockStatus": str(row.get("stockStatus", "")),
                "genderLabel": str(row.get("genderLabel", "")),
                "imageUrl": f"https://ui-avatars.com/api/?name={str(row.get('brandName', 'P'))[:2]}&background=random&size=200",
                "similarity_score": round(float(scores[i]), 4),
            })
        return results

    # ── Supabase pgvector search ──────────────────────────────
    def _supabase_search(self, query_embedding: list[float], top_n: int = 10, category: str | None = None):
        """Search via Supabase RPC match_products function."""
        client = get_supabase()
        if client is None:
            return []

        result = client.rpc("match_products", {
            "query_embedding": query_embedding,
            "match_count": top_n,
            "filter_category": category,
        }).execute()

        products = []
        for row in result.data:
            products.append({
                "id": row["id"],
                "name": row["title"],
                "brandName": row["brand"],
                "product_type": row.get("category", ""),
                "department": row.get("department", ""),
                "description_short": row.get("description_short", ""),
                "finalPrice": float(row.get("price", 0)),
                "retailPrice": float(row.get("retail_price", 0)),
                "discount_pct": round(float(row.get("discount_pct", 0)), 1),
                "rating": round(float(row.get("rating", 4.0)), 1),
                "stockStatus": row.get("stock_status", "IN_STOCK"),
                "genderLabel": row.get("gender_label", ""),
                "imageUrl": row.get("image_url", ""),
                "similarity_score": round(float(row.get("similarity", 0)), 4),
            })
        return products

    # ── Public API ────────────────────────────────────────────
    def search_similar(self, query: str, top_n: int = 10, category: str | None = None):
        """Semantic search: query text → embedding → nearest products."""
        query_vec = self.encode_query(query)

        if is_supabase_configured():
            return self._supabase_search(query_vec, top_n, category)
        else:
            return self._local_search(np.array(query_vec), top_n)

    def search_by_product(self, product_id: int, top_n: int = 10):
        """Find products similar to a given product by its index."""
        if is_supabase_configured():
            client = get_supabase()
            # Get the product's embedding from Supabase
            result = client.table("product_embeddings").select("embedding").eq(
                "product_id", product_id
            ).single().execute()
            if result.data:
                return self._supabase_search(result.data["embedding"], top_n + 1)
            return []
        else:
            # Local fallback: use cached embedding directly
            self._load_local_cache()
            if self._local_embeddings is None:
                return []
            if product_id < 0 or product_id >= len(self._local_embeddings):
                return []
            query_vec = self._local_embeddings[product_id]
            return self._local_search(query_vec, top_n, exclude_id=product_id)


# Singleton
vector_engine = VectorEngine()
