"""
Multi-Modal Product Recommendation Engine
Combines TF-IDF text features, price normalization, and brand encoding
to produce hybrid content-based recommendations using cosine similarity.
"""

import os
import pandas as pd
import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import hstack, csr_matrix

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_BACKEND_DIR)

# Model cache – use /tmp on Vercel (read-only filesystem),
# project-relative on Linux/Render, TEMP on Windows.
if os.environ.get("VERCEL"):
    MODEL_DIR = "/tmp/jomashop_models"
elif os.name == "nt":
    MODEL_DIR = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "jomashop_models")
else:
    MODEL_DIR = os.path.join(_PROJECT_DIR, "models_cache")
os.makedirs(MODEL_DIR, exist_ok=True)

# On Vercel use the smaller sampled dataset to fit within serverless limits
if os.environ.get("VERCEL"):
    DATA_PATH = os.path.join(_PROJECT_DIR, "Dataset", "vercel_products.csv")
else:
    DATA_PATH = os.path.join(_PROJECT_DIR, "Dataset", "JomaShop Products Data.csv")


class RecommendationEngine:
    def __init__(self):
        self.df = None
        self.feature_matrix = None
        self.tfidf = None
        self.price_scaler = None
        self.brand_encoder = None
        self._is_ready = False

    # ------------------------------------------------------------------ #
    #  Build / Load
    # ------------------------------------------------------------------ #
    def build(self, csv_path: str | None = None):
        """Load data, engineer features, build similarity-ready matrix."""
        csv_path = csv_path or DATA_PATH
        self.df = pd.read_csv(csv_path)
        self._clean()
        self._engineer_features()
        self._is_ready = True

    def _clean(self):
        df = self.df
        # Fill missing text
        for col in ["name", "description.short", "description.complete"]:
            df[col] = df[col].fillna("")
        df["brandName"] = df["brandName"].fillna("Unknown")
        df["pricing.finalPrice.value"] = pd.to_numeric(
            df["pricing.finalPrice.value"], errors="coerce"
        ).fillna(0)
        df["pricing.retailPrice.value"] = pd.to_numeric(
            df["pricing.retailPrice.value"], errors="coerce"
        ).fillna(0)
        # Combined text blob
        df["text_blob"] = (
            df["name"] + " " + df["description.short"] + " " + df["description.complete"]
        ).str.lower()
        # Discount percentage feature
        df["discount_pct"] = np.where(
            df["pricing.retailPrice.value"] > 0,
            (
                (df["pricing.retailPrice.value"] - df["pricing.finalPrice.value"])
                / df["pricing.retailPrice.value"]
                * 100
            ),
            0,
        )
        df["discount_pct"] = df["discount_pct"].clip(0, 100)
        # Unique row index
        df = df.reset_index(drop=True)
        self.df = df

    def _engineer_features(self):
        df = self.df
        # --- Text TF-IDF ---
        tfidf_path = os.path.join(MODEL_DIR, "tfidf.pkl")
        if os.path.exists(tfidf_path):
            self.tfidf = joblib.load(tfidf_path)
            X_text = self.tfidf.transform(df["text_blob"])
        else:
            self.tfidf = TfidfVectorizer(
                max_features=20_000,
                stop_words="english",
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            X_text = self.tfidf.fit_transform(df["text_blob"])
            joblib.dump(self.tfidf, tfidf_path)

        # --- Price scaling ---
        scaler_path = os.path.join(MODEL_DIR, "price_scaler.pkl")
        price_cols = df[["pricing.finalPrice.value", "discount_pct"]].values
        if os.path.exists(scaler_path):
            self.price_scaler = joblib.load(scaler_path)
            X_price = self.price_scaler.transform(price_cols)
        else:
            self.price_scaler = MinMaxScaler()
            X_price = self.price_scaler.fit_transform(price_cols)
            joblib.dump(self.price_scaler, scaler_path)

        # --- Brand one-hot (top 200 brands, rest → "Other") ---
        brand_path = os.path.join(MODEL_DIR, "brand_enc.pkl")
        top_brands = df["brandName"].value_counts().head(200).index.tolist()
        df["brand_clean"] = df["brandName"].where(
            df["brandName"].isin(top_brands), "Other"
        )
        if os.path.exists(brand_path):
            self.brand_encoder = joblib.load(brand_path)
        else:
            self.brand_encoder = LabelEncoder()
            self.brand_encoder.fit(df["brand_clean"])
            joblib.dump(self.brand_encoder, brand_path)
        brand_encoded = self.brand_encoder.transform(df["brand_clean"])
        n_brands = len(self.brand_encoder.classes_)
        brand_onehot = csr_matrix(
            (np.ones(len(brand_encoded)), (np.arange(len(brand_encoded)), brand_encoded)),
            shape=(len(brand_encoded), n_brands),
        )

        # --- Combine all modalities ---
        # Weight: text 1.0, price 0.3, brand 0.5
        X_price_sparse = csr_matrix(X_price * 0.3)
        brand_onehot_weighted = brand_onehot * 0.5
        self.feature_matrix = hstack([X_text, X_price_sparse, brand_onehot_weighted])

    # ------------------------------------------------------------------ #
    #  Recommend
    # ------------------------------------------------------------------ #
    def recommend_by_index(self, idx: int, top_n: int = 10):
        """Return top_n similar products for a given dataframe index."""
        if not self._is_ready:
            raise RuntimeError("Engine not built. Call build() first.")
        query_vec = self.feature_matrix[idx]
        scores = cosine_similarity(query_vec, self.feature_matrix).flatten()
        # Exclude the item itself
        scores[idx] = -1
        top_indices = scores.argsort()[::-1][:top_n]
        return self._format_results(top_indices, scores)

    def recommend_by_query(
        self, query: str, brand: str | None = None, top_n: int = 10
    ):
        """Free-text search → TF-IDF vector → cosine similarity."""
        if not self._is_ready:
            raise RuntimeError("Engine not built. Call build() first.")
        text_vec = self.tfidf.transform([query.lower()])
        # Pad with zeros for price + brand dimensions
        n_extra = self.feature_matrix.shape[1] - text_vec.shape[1]
        padding = csr_matrix((1, n_extra))
        query_vec = hstack([text_vec, padding])
        scores = cosine_similarity(query_vec, self.feature_matrix).flatten()

        # Optional brand filter boost
        if brand:
            brand_lower = brand.lower()
            brand_mask = self.df["brandName"].str.lower().eq(brand_lower).values.astype(float)
            scores = scores + brand_mask * 0.15  # boost matching brand

        top_indices = scores.argsort()[::-1][:top_n]
        return self._format_results(top_indices, scores)

    def recommend_batch(self, queries_df: pd.DataFrame, top_n: int = 5):
        """Process a DataFrame with 'query' (and optional 'brand') columns."""
        results = []
        for _, row in queries_df.iterrows():
            query = str(row.get("query", row.get("name", "")))
            brand = str(row.get("brand", row.get("brandName", ""))) or None
            if brand and brand.lower() in ("nan", "none", ""):
                brand = None
            recs = self.recommend_by_query(query, brand=brand, top_n=top_n)
            for rec in recs:
                rec["source_query"] = query
            results.extend(recs)
        return results

    def get_products(self, page: int = 1, per_page: int = 20, search: str | None = None):
        """Paginated product catalog."""
        df = self.df
        if search:
            mask = df["text_blob"].str.contains(search.lower(), na=False)
            df = df[mask]
        total = len(df)
        start = (page - 1) * per_page
        end = start + per_page
        subset = df.iloc[start:end]
        products = []
        for idx, row in subset.iterrows():
            products.append(self._row_to_dict(idx, row))
        return {
            "products": products,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }

    def get_product_by_index(self, idx: int):
        if idx < 0 or idx >= len(self.df):
            return None
        row = self.df.iloc[idx]
        return self._row_to_dict(idx, row)

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #
    def _format_results(self, indices, scores):
        results = []
        for i in indices:
            row = self.df.iloc[i]
            d = self._row_to_dict(i, row)
            d["similarity_score"] = round(float(scores[i]), 4)
            results.append(d)
        return results

    def _row_to_dict(self, idx, row):
        return {
            "id": int(idx),
            "name": str(row.get("name", "")),
            "brandName": str(row.get("brandName", "")),
            "product_type": str(row.get("product_type", "")),
            "description_short": str(row.get("description.short", "")),
            "finalPrice": float(row.get("pricing.finalPrice.value", 0)),
            "retailPrice": float(row.get("pricing.retailPrice.value", 0)),
            "discount_pct": round(float(row.get("discount_pct", 0)), 1),
            "stockStatus": str(row.get("stockStatus", "")),
            "genderLabel": str(row.get("genderLabel", "")),
            "department": str(row.get("department", "")),
            "imageUrl": f"https://ui-avatars.com/api/?name={str(row.get('brandName', 'P'))[:2]}&background=random&size=200",
        }
