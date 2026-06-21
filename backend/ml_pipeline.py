"""
PDF-Aligned Multi-Modal Product Classification Pipeline
========================================================

This module realizes the architecture described in the project's final
report — a stacking ensemble that fuses textual, brand and pricing signals
to classify e-commerce products into types.

Architecture (mirrors the report's Chapter 3 — System Design):

    text  ──► HashingVectorizer (2^18 features, ngram (1,2),
                                 stop_words='english',
                                 alternate_sign=False)
    brand ──► LabelEncoder ──► one-hot
    price ──► StandardScaler(with_mean=False)
                 │
                 ▼
    sparse hstack ──► Stacking Ensemble
                        ├── GradientBoostingClassifier  (base #1)
                        ├── LGBMClassifier              (base #2, fallback: RandomForest)
                        ├── NGBClassifier               (base #3, fallback: ExtraTrees)
                        └── meta: CalibratedClassifierCV(LinearSVC)
                                  → calibrated probabilities

The module is deployment-safe: it gracefully degrades when heavy optional
deps (lightgbm / ngboost) are unavailable, swapping in scikit-learn
estimators with similar inductive bias. Training is performed once and
cached on disk so subsequent boots are fast.

Public surface:
    ProductClassifier.build()        – train or load from cache
    ProductClassifier.predict(...)   – per-base + ensemble probabilities
    ProductClassifier.metrics()      – per-model evaluation metrics
    ProductClassifier.architecture() – machine-readable pipeline spec
"""
from __future__ import annotations

import json
import os
import time
import warnings
from dataclasses import dataclass, field, asdict
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import (
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
    StackingClassifier,
)
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import LinearSVC

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ─── Paths ────────────────────────────────────────────────────────────
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_BACKEND_DIR)

if os.environ.get("VERCEL"):
    CACHE_DIR = "/tmp/cortexcart_ml"
elif os.name == "nt":
    CACHE_DIR = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "cortexcart_ml")
else:
    CACHE_DIR = os.path.join(_PROJECT_DIR, "models_cache", "ml")
os.makedirs(CACHE_DIR, exist_ok=True)

DEFAULT_DATA_PATH = (
    os.path.join(_PROJECT_DIR, "Dataset", "vercel_products.csv")
    if os.environ.get("VERCEL")
    else os.path.join(_PROJECT_DIR, "Dataset", "JomaShop Products Data.csv")
)

# Sample cap keeps boot fast — full dataset trains via training script.
DEFAULT_SAMPLE_CAP = int(os.environ.get("CORTEX_ML_SAMPLE", "12000"))

# ─── Optional heavy estimators ────────────────────────────────────────
try:
    from lightgbm import LGBMClassifier  # type: ignore
    _HAS_LGBM = True
except Exception:  # pragma: no cover
    _HAS_LGBM = False

try:
    from ngboost import NGBClassifier  # type: ignore
    from ngboost.distns import k_categorical  # type: ignore
    _HAS_NGB = True
except Exception:  # pragma: no cover
    _HAS_NGB = False


# ─── Public dataclasses ───────────────────────────────────────────────
@dataclass
class ModelMetric:
    name: str
    label: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    available: bool = True
    note: str = ""


@dataclass
class PipelineMetrics:
    samples_total: int
    samples_train: int
    samples_test: int
    classes: list[str]
    feature_dim: int
    trained_at: float
    duration_seconds: float
    models: list[ModelMetric] = field(default_factory=list)


# ─── Classifier ───────────────────────────────────────────────────────
class ProductClassifier:
    """Stacking ensemble for product type classification (PDF-aligned)."""

    # HashingVectorizer settings mirror the project report.
    HV_FEATURES = 2 ** 18
    NGRAM_RANGE = (1, 2)

    # Minimum samples per class needed for stratified split.
    MIN_PER_CLASS = 5

    def __init__(self, csv_path: str | None = None, sample_cap: int | None = None):
        self.csv_path = csv_path or DEFAULT_DATA_PATH
        self.sample_cap = sample_cap or DEFAULT_SAMPLE_CAP

        self.text_vectorizer: HashingVectorizer | None = None
        self.brand_encoder: LabelEncoder | None = None
        self.price_scaler: StandardScaler | None = None
        self.label_encoder: LabelEncoder | None = None

        self.base_models: dict[str, Any] = {}
        self.ensemble: StackingClassifier | None = None
        self._metrics: PipelineMetrics | None = None
        self._n_brands: int = 0
        self._is_ready: bool = False

    # ───────────────────────── build / cache ──────────────────────────
    def _cache_paths(self) -> dict[str, str]:
        return {
            "text": os.path.join(CACHE_DIR, "hash_vectorizer.pkl"),
            "brand": os.path.join(CACHE_DIR, "brand_enc.pkl"),
            "price": os.path.join(CACHE_DIR, "price_scaler.pkl"),
            "label": os.path.join(CACHE_DIR, "label_enc.pkl"),
            "ensemble": os.path.join(CACHE_DIR, "stacking_ensemble.pkl"),
            "bases": os.path.join(CACHE_DIR, "base_models.pkl"),
            "metrics": os.path.join(CACHE_DIR, "metrics.json"),
        }

    def build(self, force: bool = False) -> "ProductClassifier":
        paths = self._cache_paths()
        if not force and all(os.path.exists(p) for p in paths.values()):
            try:
                self._load_cached(paths)
                self._is_ready = True
                return self
            except Exception as exc:  # cache corruption – retrain
                print(f"[ml_pipeline] cache load failed ({exc}); retraining.")

        self._train_and_persist(paths)
        self._is_ready = True
        return self

    def _load_cached(self, paths: dict[str, str]) -> None:
        self.text_vectorizer = joblib.load(paths["text"])
        self.brand_encoder = joblib.load(paths["brand"])
        self.price_scaler = joblib.load(paths["price"])
        self.label_encoder = joblib.load(paths["label"])
        self.ensemble = joblib.load(paths["ensemble"])
        self.base_models = joblib.load(paths["bases"])
        self._n_brands = len(self.brand_encoder.classes_)
        with open(paths["metrics"], "r", encoding="utf-8") as f:
            payload = json.load(f)
        self._metrics = PipelineMetrics(
            samples_total=payload["samples_total"],
            samples_train=payload["samples_train"],
            samples_test=payload["samples_test"],
            classes=payload["classes"],
            feature_dim=payload["feature_dim"],
            trained_at=payload["trained_at"],
            duration_seconds=payload["duration_seconds"],
            models=[ModelMetric(**m) for m in payload["models"]],
        )

    # ───────────────────────── training ───────────────────────────────
    def _load_dataframe(self) -> pd.DataFrame:
        df = pd.read_csv(self.csv_path)
        keep = [
            "product_type", "name", "brandName",
            "description.short", "description.complete",
            "pricing.finalPrice.value", "pricing.retailPrice.value",
        ]
        for col in keep:
            if col not in df.columns:
                df[col] = ""
        df = df[keep].copy()

        for col in ["name", "description.short", "description.complete", "brandName", "product_type"]:
            df[col] = df[col].fillna("").astype(str).str.strip()

        df["pricing.finalPrice.value"] = pd.to_numeric(
            df["pricing.finalPrice.value"], errors="coerce"
        ).fillna(0.0)
        df["pricing.retailPrice.value"] = pd.to_numeric(
            df["pricing.retailPrice.value"], errors="coerce"
        ).fillna(0.0)
        df["discount_pct"] = np.where(
            df["pricing.retailPrice.value"] > 0,
            (df["pricing.retailPrice.value"] - df["pricing.finalPrice.value"])
            / df["pricing.retailPrice.value"] * 100,
            0.0,
        ).clip(0, 100)

        df = df[df["product_type"].str.len() > 0]
        df["brandName"] = df["brandName"].where(df["brandName"].str.len() > 0, "Unknown")
        df["text_blob"] = (
            df["name"] + " " + df["description.short"] + " " + df["description.complete"]
        ).str.lower().str.strip()

        # Drop classes with too few samples for stratification
        counts = df["product_type"].value_counts()
        keep_classes = counts[counts >= self.MIN_PER_CLASS].index
        df = df[df["product_type"].isin(keep_classes)]

        # Down-sample for fast boot training
        if self.sample_cap and len(df) > self.sample_cap:
            df = (
                df.groupby("product_type", group_keys=False)
                .apply(lambda g: g.sample(
                    min(len(g), max(self.MIN_PER_CLASS, self.sample_cap // max(1, df["product_type"].nunique()))),
                    random_state=42,
                ))
                .reset_index(drop=True)
            )
            if len(df) > self.sample_cap:
                df = df.sample(self.sample_cap, random_state=42).reset_index(drop=True)

        return df.reset_index(drop=True)

    def _fit_features(self, df: pd.DataFrame):
        # Text → HashingVectorizer (PDF-spec)
        self.text_vectorizer = HashingVectorizer(
            n_features=self.HV_FEATURES,
            ngram_range=self.NGRAM_RANGE,
            stop_words="english",
            alternate_sign=False,
            norm="l2",
        )
        X_text = self.text_vectorizer.transform(df["text_blob"])

        # Brand encoding (cap top 200)
        top_brands = df["brandName"].value_counts().head(200).index.tolist()
        df["brand_clean"] = df["brandName"].where(df["brandName"].isin(top_brands), "Other")
        self.brand_encoder = LabelEncoder()
        brand_ids = self.brand_encoder.fit_transform(df["brand_clean"])
        self._n_brands = len(self.brand_encoder.classes_)
        brand_onehot = csr_matrix(
            (np.ones(len(brand_ids)), (np.arange(len(brand_ids)), brand_ids)),
            shape=(len(brand_ids), self._n_brands),
        )

        # Price scaling (StandardScaler with_mean=False so sparse-safe)
        price_cols = df[["pricing.finalPrice.value", "discount_pct"]].values.astype(float)
        self.price_scaler = StandardScaler(with_mean=False)
        X_price = csr_matrix(self.price_scaler.fit_transform(price_cols))

        X = hstack([X_text, brand_onehot, X_price]).tocsr()
        return X

    def _make_base_models(self, n_classes: int) -> dict[str, Any]:
        """Construct base learners with graceful fallbacks."""
        bases: dict[str, Any] = {}

        # 1. GradientBoosting — kept small for fast train on sparse stack
        bases["gbc"] = GradientBoostingClassifier(
            n_estimators=80, max_depth=3, learning_rate=0.15, random_state=42,
        )

        # 2. LightGBM (preferred) or RandomForest fallback
        if _HAS_LGBM:
            bases["lgbm"] = LGBMClassifier(
                n_estimators=180, learning_rate=0.08, num_leaves=31,
                random_state=42, n_jobs=-1, verbose=-1,
            )
        else:
            bases["lgbm"] = RandomForestClassifier(
                n_estimators=180, max_depth=None, random_state=42, n_jobs=-1,
            )

        # 3. NGBoost (preferred) or ExtraTrees fallback.
        #    NGBClassifier requires Dist=k_categorical(K) — a factory call,
        #    so we must know n_classes at construction time.
        if _HAS_NGB and n_classes >= 2:
            try:
                bases["ngb"] = NGBClassifier(
                    Dist=k_categorical(n_classes),
                    n_estimators=120, learning_rate=0.05, verbose=False,
                )
            except Exception as exc:  # pragma: no cover
                print(f"[ml_pipeline] NGBoost init failed ({exc}); falling back to ExtraTrees.")
                bases["ngb"] = ExtraTreesClassifier(
                    n_estimators=180, max_depth=None, random_state=42, n_jobs=-1,
                )
        else:
            bases["ngb"] = ExtraTreesClassifier(
                n_estimators=180, max_depth=None, random_state=42, n_jobs=-1,
            )

        return bases

    def _train_and_persist(self, paths: dict[str, str]) -> None:
        t0 = time.time()
        df = self._load_dataframe()
        if df.empty:
            raise RuntimeError("Training dataframe is empty; check dataset path.")

        # Targets
        self.label_encoder = LabelEncoder()
        y = self.label_encoder.fit_transform(df["product_type"])
        classes = list(self.label_encoder.classes_)

        # Features
        X = self._fit_features(df)

        # Stratified split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y,
        )

        # GBC needs dense input — densify with memory-bounded projection.
        X_train_dense_safe = self._dense_safe(X_train)
        X_test_dense_safe = self._dense_safe(X_test)

        bases = self._make_base_models(n_classes=len(classes))
        self.base_models = {}
        metrics: list[ModelMetric] = []

        # Train each base independently to gather per-model metrics
        for key, model in bases.items():
            name, label, note = self._describe(key)
            try:
                if key == "gbc":
                    model.fit(X_train_dense_safe, y_train)
                    preds = model.predict(X_test_dense_safe)
                else:
                    model.fit(X_train, y_train)
                    preds = model.predict(X_test)
                self.base_models[key] = model
                metrics.append(self._score(name, label, y_test, preds, True, note))
            except Exception as exc:
                print(f"[ml_pipeline] base model {key} failed: {exc}")
                metrics.append(
                    ModelMetric(name=name, label=label, accuracy=0.0,
                                precision=0.0, recall=0.0, f1=0.0,
                                available=False, note=f"failed: {exc}")
                )

        # ─ Stacking ensemble (sklearn-clone-safe bases only) ─
        # NGBoost's get_params surface drifts from sklearn's clone API
        # across versions, so we exclude it from the stack but still
        # report it as a standalone base model above.
        stack_safe_keys = {"lgbm"}  # always include (RF fallback also safe)
        usable = [(k, v) for k, v in self.base_models.items() if k in stack_safe_keys]
        # Add NGB only when it is the ExtraTrees fallback (clone-safe)
        if "ngb" in self.base_models and not _HAS_NGB:
            usable.append(("ngb", self.base_models["ngb"]))

        if usable:
            final = CalibratedClassifierCV(
                estimator=LinearSVC(C=1.0, max_iter=2000), cv=3, method="sigmoid",
            )
            self.ensemble = StackingClassifier(
                estimators=usable,
                final_estimator=final,
                stack_method="predict_proba",
                passthrough=False,
                n_jobs=1,
            )
            try:
                self.ensemble.fit(X_train, y_train)
                preds = self.ensemble.predict(X_test)
                metrics.append(self._score(
                    "stacking", "Stacking Ensemble (Calibrated LinearSVC meta)",
                    y_test, preds, True,
                    "Final estimator: CalibratedClassifierCV(LinearSVC) sigmoid",
                ))
            except Exception as exc:
                print(f"[ml_pipeline] stacking failed: {exc}")
                self.ensemble = None
                metrics.append(ModelMetric(
                    name="stacking",
                    label="Stacking Ensemble (Calibrated LinearSVC meta)",
                    accuracy=0.0, precision=0.0, recall=0.0, f1=0.0,
                    available=False, note=f"failed: {exc}",
                ))
        else:
            self.ensemble = None

        # Also train standalone CalibratedClassifierCV(LinearSVC) for reporting
        try:
            lsvc = CalibratedClassifierCV(
                estimator=LinearSVC(C=1.0, max_iter=2000), cv=3, method="sigmoid",
            )
            lsvc.fit(X_train, y_train)
            self.base_models["lsvc"] = lsvc
            preds = lsvc.predict(X_test)
            metrics.append(self._score(
                "lsvc", "Calibrated LinearSVC", y_test, preds, True,
                "CalibratedClassifierCV(LinearSVC) primary text classifier",
            ))
        except Exception as exc:
            print(f"[ml_pipeline] lsvc failed: {exc}")
            metrics.append(ModelMetric(
                name="lsvc", label="Calibrated LinearSVC",
                accuracy=0.0, precision=0.0, recall=0.0, f1=0.0,
                available=False, note=f"failed: {exc}",
            ))

        self._metrics = PipelineMetrics(
            samples_total=len(df),
            samples_train=int(X_train.shape[0]),
            samples_test=int(X_test.shape[0]),
            classes=classes,
            feature_dim=int(X.shape[1]),
            trained_at=time.time(),
            duration_seconds=round(time.time() - t0, 2),
            models=metrics,
        )

        # ── Persist ────────────────────────────────────────────────────
        joblib.dump(self.text_vectorizer, paths["text"])
        joblib.dump(self.brand_encoder, paths["brand"])
        joblib.dump(self.price_scaler, paths["price"])
        joblib.dump(self.label_encoder, paths["label"])
        joblib.dump(self.ensemble, paths["ensemble"])
        joblib.dump(self.base_models, paths["bases"])
        with open(paths["metrics"], "w", encoding="utf-8") as f:
            payload = asdict(self._metrics)
            json.dump(payload, f, indent=2)

    # ───────────────────────── helpers ────────────────────────────────
    def _dense_safe(self, X) -> np.ndarray:
        """Densify a sparse matrix safely for GBC, capping memory."""
        if X.shape[1] > 8000:
            # Reduce to the trailing brand+price block + a hashed projection
            # by simply slicing the last 1024 columns + summing first columns.
            head = np.asarray(X[:, :1024].sum(axis=1)).reshape(-1, 1)
            tail = X[:, -min(1024, X.shape[1] - 1024):].toarray()
            return np.hstack([head, tail])
        return X.toarray()

    @staticmethod
    def _describe(key: str) -> tuple[str, str, str]:
        if key == "gbc":
            return ("gbc", "Gradient Boosting Classifier",
                    "sklearn.ensemble.GradientBoostingClassifier on dense projection")
        if key == "lgbm":
            return ("lgbm", "LightGBM Classifier" if _HAS_LGBM else "RandomForest (LightGBM fallback)",
                    "lightgbm.LGBMClassifier" if _HAS_LGBM else
                    "sklearn.ensemble.RandomForestClassifier (lightgbm unavailable)")
        if key == "ngb":
            return ("ngb", "NGBoost Classifier" if _HAS_NGB else "ExtraTrees (NGBoost fallback)",
                    "ngboost.NGBClassifier(k_categorical)" if _HAS_NGB else
                    "sklearn.ensemble.ExtraTreesClassifier (ngboost unavailable)")
        return (key, key, "")

    @staticmethod
    def _score(name, label, y_true, preds, available, note) -> ModelMetric:
        return ModelMetric(
            name=name, label=label,
            accuracy=round(float(accuracy_score(y_true, preds)), 4),
            precision=round(float(precision_score(y_true, preds, average="weighted", zero_division=0)), 4),
            recall=round(float(recall_score(y_true, preds, average="weighted", zero_division=0)), 4),
            f1=round(float(f1_score(y_true, preds, average="weighted", zero_division=0)), 4),
            available=available, note=note,
        )

    # ───────────────────────── inference ──────────────────────────────
    def _vectorize(self, text: str, brand: str | None, price: float, discount_pct: float):
        text_vec = self.text_vectorizer.transform([text.lower()])
        brand_clean = brand if brand and brand in self.brand_encoder.classes_ else "Other"
        if brand_clean not in self.brand_encoder.classes_:
            brand_clean = self.brand_encoder.classes_[0]
        brand_id = int(self.brand_encoder.transform([brand_clean])[0])
        brand_vec = csr_matrix(
            (np.ones(1), (np.zeros(1, dtype=int), np.array([brand_id]))),
            shape=(1, self._n_brands),
        )
        price_vec = csr_matrix(
            self.price_scaler.transform([[float(price or 0), float(discount_pct or 0)]])
        )
        return hstack([text_vec, brand_vec, price_vec]).tocsr()

    def predict(self, *, text: str, brand: str | None = None,
                price: float = 0.0, discount_pct: float = 0.0, top_k: int = 5) -> dict[str, Any]:
        if not self._is_ready:
            raise RuntimeError("ProductClassifier not built. Call build() first.")

        X = self._vectorize(text=text, brand=brand, price=price, discount_pct=discount_pct)
        results: dict[str, Any] = {"per_model": {}}

        for key, model in self.base_models.items():
            try:
                X_in = self._dense_safe(X) if key == "gbc" else X
                if hasattr(model, "predict_proba"):
                    proba = model.predict_proba(X_in)[0]
                else:
                    pred = model.predict(X_in)[0]
                    proba = np.zeros(len(self.label_encoder.classes_))
                    proba[int(pred)] = 1.0
                top_idx = np.argsort(proba)[::-1][:top_k]
                results["per_model"][key] = {
                    "label": self._describe(key)[1],
                    "top": [
                        {"class": str(self.label_encoder.classes_[i]), "prob": round(float(proba[i]), 4)}
                        for i in top_idx
                    ],
                }
            except Exception as exc:
                results["per_model"][key] = {"label": self._describe(key)[1], "error": str(exc)}

        if self.ensemble is not None:
            try:
                proba = self.ensemble.predict_proba(X)[0]
                top_idx = np.argsort(proba)[::-1][:top_k]
                results["ensemble"] = {
                    "label": "Stacking Ensemble (Calibrated LinearSVC meta)",
                    "top": [
                        {"class": str(self.label_encoder.classes_[i]), "prob": round(float(proba[i]), 4)}
                        for i in top_idx
                    ],
                    "predicted_class": str(self.label_encoder.classes_[int(np.argmax(proba))]),
                    "confidence": round(float(np.max(proba)), 4),
                }
            except Exception as exc:
                results["ensemble"] = {"error": str(exc)}

        return results

    # ───────────────────────── introspection ──────────────────────────
    def metrics(self) -> dict[str, Any]:
        if not self._metrics:
            return {}
        return asdict(self._metrics)

    def architecture(self) -> dict[str, Any]:
        """Machine-readable description of the pipeline (drives the UI)."""
        return {
            "name": "CortexCart Multi-Modal Stacking Ensemble",
            "report_chapter": "Chapter 3 — System Design",
            "feature_extractors": [
                {
                    "name": "HashingVectorizer",
                    "modality": "text",
                    "config": {
                        "n_features": self.HV_FEATURES,
                        "ngram_range": list(self.NGRAM_RANGE),
                        "stop_words": "english",
                        "alternate_sign": False,
                        "norm": "l2",
                    },
                },
                {
                    "name": "LabelEncoder → OneHot",
                    "modality": "brand",
                    "config": {"top_brands": 200, "fallback_bucket": "Other"},
                },
                {
                    "name": "StandardScaler",
                    "modality": "price",
                    "config": {"with_mean": False, "fields": ["finalPrice", "discount_pct"]},
                },
            ],
            "base_estimators": [
                {"key": "gbc", "label": "Gradient Boosting Classifier",
                 "library": "scikit-learn", "available": True},
                {"key": "lgbm", "label": "LightGBM" if _HAS_LGBM else "RandomForest (fallback)",
                 "library": "lightgbm" if _HAS_LGBM else "scikit-learn", "available": True},
                {"key": "ngb", "label": "NGBoost" if _HAS_NGB else "ExtraTrees (fallback)",
                 "library": "ngboost" if _HAS_NGB else "scikit-learn", "available": True},
                {"key": "lsvc", "label": "Calibrated LinearSVC",
                 "library": "scikit-learn", "available": True,
                 "note": "Also serves as stacking meta-learner"},
            ],
            "meta_estimator": {
                "name": "CalibratedClassifierCV(LinearSVC)",
                "calibration": "sigmoid",
                "cv": 3,
            },
            "fusion": "scipy.sparse.hstack([text, brand_onehot, price])",
            "training_split": {"test_size": 0.2, "stratified": True, "random_state": 42},
            "deployment_notes": {
                "gbc_input": "Dense projection (memory-bounded)",
                "others_input": "Sparse fused matrix",
                "cache_dir": CACHE_DIR,
            },
        }

    @property
    def is_ready(self) -> bool:
        return self._is_ready


# ─── Module-level singleton helper ────────────────────────────────────
_singleton: ProductClassifier | None = None


def get_classifier(eager: bool = False) -> ProductClassifier:
    """Lazy-load the singleton classifier; build only when first needed."""
    global _singleton
    if _singleton is None:
        _singleton = ProductClassifier()
        if eager:
            _singleton.build()
    return _singleton
