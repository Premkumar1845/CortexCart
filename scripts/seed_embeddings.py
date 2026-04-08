"""
CortexCart – Embedding Pipeline
Loads products from CSV, generates vector embeddings using sentence-transformers,
and uploads to Supabase (products + product_embeddings tables).

Usage:
    pip install sentence-transformers supabase python-dotenv pandas
    python scripts/seed_embeddings.py
"""

import os
import sys
import uuid
import json
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Load environment
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
load_dotenv(os.path.join(_PROJECT_DIR, ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
DATA_PATH = os.path.join(_PROJECT_DIR, "Dataset", "JomaShop Products Data.csv")
BATCH_SIZE = 100  # rows per Supabase insert


def load_data(csv_path: str, max_rows: int | None = None) -> pd.DataFrame:
    """Load and clean the product CSV."""
    print(f"📂  Loading data from {csv_path}")
    df = pd.read_csv(csv_path)
    if max_rows:
        df = df.head(max_rows)

    for col in ["name", "description.short", "description.complete"]:
        df[col] = df[col].fillna("")
    df["brandName"] = df["brandName"].fillna("Unknown")
    df["product_type"] = df["product_type"].fillna("")
    df["stockStatus"] = df["stockStatus"].fillna("IN_STOCK")
    df["genderLabel"] = df["genderLabel"].fillna("")
    df["department"] = df["department"].fillna("")

    df["pricing.finalPrice.value"] = pd.to_numeric(
        df["pricing.finalPrice.value"], errors="coerce"
    ).fillna(0)
    df["pricing.retailPrice.value"] = pd.to_numeric(
        df["pricing.retailPrice.value"], errors="coerce"
    ).fillna(0)

    df["discount_pct"] = np.where(
        df["pricing.retailPrice.value"] > 0,
        (
            (df["pricing.retailPrice.value"] - df["pricing.finalPrice.value"])
            / df["pricing.retailPrice.value"]
            * 100
        ),
        0,
    )
    df["discount_pct"] = df["discount_pct"].clip(0, 100).round(1)

    # Build text blob for embedding
    df["text_blob"] = (
        df["name"] + " " + df["brandName"] + " " + df["product_type"] + " "
        + df["department"] + " " + df["description.short"]
    ).str.strip()

    print(f"✅  Loaded {len(df)} products")
    return df


def generate_embeddings(texts: list[str], batch_size: int = 256) -> np.ndarray:
    """Generate embeddings using sentence-transformers (all-MiniLM-L6-v2, dim=384)."""
    from sentence_transformers import SentenceTransformer

    print("🧠  Loading sentence-transformer model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"🔄  Generating embeddings for {len(texts)} products...")
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    print(f"✅  Generated {embeddings.shape[0]} embeddings (dim={embeddings.shape[1]})")
    return embeddings


def upload_to_supabase(df: pd.DataFrame, embeddings: np.ndarray):
    """Upload products and embeddings to Supabase."""
    from supabase import create_client

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌  SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)

    print("☁️  Connecting to Supabase...")
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Upload products in batches
    print(f"📤  Uploading {len(df)} products...")
    product_ids = []

    for start in range(0, len(df), BATCH_SIZE):
        end = min(start + BATCH_SIZE, len(df))
        batch = df.iloc[start:end]

        rows = []
        batch_ids = []
        for _, row in batch.iterrows():
            pid = str(uuid.uuid4())
            batch_ids.append(pid)
            rows.append({
                "id": pid,
                "title": str(row["name"])[:500],
                "brand": str(row["brandName"]),
                "category": str(row["product_type"]),
                "department": str(row["department"]),
                "gender_label": str(row["genderLabel"]),
                "price": float(row["pricing.finalPrice.value"]),
                "retail_price": float(row["pricing.retailPrice.value"]),
                "discount_pct": float(row["discount_pct"]),
                "rating": round(np.random.uniform(3.5, 5.0), 1),  # synthetic rating
                "stock_status": str(row["stockStatus"]),
                "image_url": f"https://ui-avatars.com/api/?name={str(row['brandName'])[:2]}&background=random&size=200",
                "description_short": str(row["description.short"])[:500],
                "description_complete": str(row.get("description.complete", ""))[:2000],
                "attributes": json.dumps({
                    "product_type": str(row["product_type"]),
                    "gender": str(row["genderLabel"]),
                }),
            })

        try:
            client.table("products").insert(rows).execute()
            product_ids.extend(batch_ids)
            print(f"  ✅  Products {start+1}–{end} uploaded")
        except Exception as e:
            print(f"  ❌  Error uploading products {start+1}–{end}: {e}")
            # Still track IDs so embedding upload aligns
            product_ids.extend(batch_ids)

    # Upload embeddings in batches
    print(f"📤  Uploading {len(embeddings)} embeddings...")
    for start in range(0, len(embeddings), BATCH_SIZE):
        end = min(start + BATCH_SIZE, len(embeddings))

        emb_rows = []
        for i in range(start, end):
            emb_rows.append({
                "product_id": product_ids[i],
                "embedding": embeddings[i].tolist(),
            })

        try:
            client.table("product_embeddings").insert(emb_rows).execute()
            print(f"  ✅  Embeddings {start+1}–{end} uploaded")
        except Exception as e:
            print(f"  ❌  Error uploading embeddings {start+1}–{end}: {e}")

    print(f"\n🎉  Done! Uploaded {len(product_ids)} products with embeddings to Supabase.")


def save_local_cache(df: pd.DataFrame, embeddings: np.ndarray):
    """Save embeddings locally as a fallback (when Supabase is not configured)."""
    import joblib

    cache_dir = os.path.join(_PROJECT_DIR, "models_cache")
    os.makedirs(cache_dir, exist_ok=True)

    emb_path = os.path.join(cache_dir, "embeddings.npy")
    meta_path = os.path.join(cache_dir, "product_meta.pkl")

    np.save(emb_path, embeddings)
    joblib.dump(df.reset_index(drop=True), meta_path)
    print(f"💾  Saved local cache: {emb_path}, {meta_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CortexCart Embedding Pipeline")
    parser.add_argument("--csv", default=DATA_PATH, help="Path to product CSV")
    parser.add_argument("--max-rows", type=int, default=None, help="Limit rows (for testing)")
    parser.add_argument("--local-only", action="store_true", help="Skip Supabase, save locally only")
    args = parser.parse_args()

    df = load_data(args.csv, max_rows=args.max_rows)
    embeddings = generate_embeddings(df["text_blob"].tolist())

    save_local_cache(df, embeddings)

    if not args.local_only:
        upload_to_supabase(df, embeddings)
    else:
        print("⏭️  Skipped Supabase upload (--local-only)")
