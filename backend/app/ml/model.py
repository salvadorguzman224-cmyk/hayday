"""
XGBoost-based hay price forecast model.

Three quantile models (q10, q50, q90) are trained per segment
(region × hay_type × grade × horizon_weeks).  Models are saved
to disk in MODEL_DIR and loaded lazily at inference time.
"""
from __future__ import annotations

import json
import logging
import os
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_percentage_error

from app.config import settings
from app.ml.features import FEATURE_COLS

logger = logging.getLogger(__name__)

MODEL_DIR = Path(settings.MODEL_DIR)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

QUANTILES = [0.025, 0.10, 0.50, 0.90, 0.975]  # q indices 0-4
QUANTILE_LABELS = ["q025", "q10", "q50", "q90", "q975"]

XGB_PARAMS_BASE = {
    "n_estimators": 300,
    "max_depth": 5,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 3,
    "tree_method": "hist",
    "random_state": 42,
}


def _model_path(segment_key: str, quantile_label: str, horizon: int) -> Path:
    safe = segment_key.replace("/", "_")
    return MODEL_DIR / f"{safe}__h{horizon}__{quantile_label}.pkl"


def _meta_path(segment_key: str, horizon: int) -> Path:
    safe = segment_key.replace("/", "_")
    return MODEL_DIR / f"{safe}__h{horizon}__meta.json"


def train_segment(
    X: pd.DataFrame,
    y: pd.Series,
    segment_key: str,
    horizon: int,
) -> dict[str, Any]:
    """
    Train all quantile models for a single segment and horizon.
    Returns a metadata dict with MAPE on a 20% holdout.
    """
    available_features = [c for c in FEATURE_COLS if c in X.columns]
    X = X[available_features]

    n = len(X)
    split = int(n * 0.8)
    X_train, X_val = X.iloc[:split], X.iloc[split:]
    y_train, y_val = y.iloc[:split], y.iloc[split:]

    models: dict[str, xgb.XGBRegressor] = {}
    for label, q in zip(QUANTILE_LABELS, QUANTILES):
        model = xgb.XGBRegressor(
            **XGB_PARAMS_BASE,
            objective="reg:quantileerror",
            quantile_alpha=q,
        )
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )
        path = _model_path(segment_key, label, horizon)
        with open(path, "wb") as f:
            pickle.dump(model, f)
        models[label] = model

    # Evaluate median model on validation set
    y_pred_val = models["q50"].predict(X_val)
    mape = float(mean_absolute_percentage_error(y_val, y_pred_val))

    # Feature importance from the q50 model
    importance = {
        feat: float(score)
        for feat, score in zip(
            available_features,
            models["q50"].feature_importances_,
        )
    }
    # Sort descending, top 10
    importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10])

    meta = {
        "segment_key": segment_key,
        "horizon": horizon,
        "n_train": split,
        "n_val": n - split,
        "mape": mape,
        "feature_importance": importance,
        "features": available_features,
        "model_version": f"xgb-v1-h{horizon}",
    }

    with open(_meta_path(segment_key, horizon), "w") as f:
        json.dump(meta, f, indent=2)

    logger.info(
        "Trained %s h=%d | MAPE=%.3f | n=%d",
        segment_key, horizon, mape, n
    )
    return meta


def load_models(segment_key: str, horizon: int) -> dict[str, xgb.XGBRegressor] | None:
    """Load all quantile models for a segment from disk."""
    models: dict[str, xgb.XGBRegressor] = {}
    for label in QUANTILE_LABELS:
        path = _model_path(segment_key, label, horizon)
        if not path.exists():
            return None
        with open(path, "rb") as f:
            models[label] = pickle.load(f)
    return models


def load_meta(segment_key: str, horizon: int) -> dict[str, Any] | None:
    path = _meta_path(segment_key, horizon)
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def predict(
    models: dict[str, xgb.XGBRegressor],
    X_row: pd.DataFrame,
) -> dict[str, float]:
    """
    Run inference with all quantile models.
    Returns a dict with predicted price + confidence bounds.
    """
    results: dict[str, float] = {}
    for label, model in models.items():
        pred = float(model.predict(X_row)[0])
        results[label] = max(0.0, pred)

    return {
        "price_predicted": results["q50"],
        "price_low_80": results["q10"],
        "price_high_80": results["q90"],
        "price_low_95": results["q025"],
        "price_high_95": results["q975"],
    }
