"""
Train the PDF-aligned multi-modal stacking ensemble.

Usage:
    python scripts/train_classifier.py                # default (cached sample)
    python scripts/train_classifier.py --force        # retrain even if cached
    python scripts/train_classifier.py --sample 25000 # custom sample cap
    python scripts/train_classifier.py --full         # train on the full CSV

Outputs are written under <project>/models_cache/ml/ and reused by the
Flask backend at boot time.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# Allow running from project root: `python scripts/train_classifier.py`
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_PROJECT, "backend"))

from ml_pipeline import ProductClassifier  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Retrain even if cache exists")
    parser.add_argument("--sample", type=int, default=None, help="Sample cap (rows)")
    parser.add_argument("--full", action="store_true", help="Train on full dataset")
    parser.add_argument("--csv", type=str, default=None, help="Override CSV path")
    args = parser.parse_args()

    sample_cap = args.sample
    if args.full:
        sample_cap = None  # disables sampling
    clf = ProductClassifier(csv_path=args.csv, sample_cap=sample_cap or 0 if args.full else sample_cap)
    print("⏳  Training PDF-aligned stacking ensemble …")
    clf.build(force=args.force)
    metrics = clf.metrics()
    print("✅  Training complete.\n")
    print(json.dumps({
        "samples": {
            "total": metrics.get("samples_total"),
            "train": metrics.get("samples_train"),
            "test": metrics.get("samples_test"),
        },
        "feature_dim": metrics.get("feature_dim"),
        "classes": len(metrics.get("classes", [])),
        "duration_seconds": metrics.get("duration_seconds"),
        "models": [
            {"name": m["name"], "accuracy": m["accuracy"], "f1": m["f1"]}
            for m in metrics.get("models", [])
        ],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
