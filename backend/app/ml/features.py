"""
Feature engineering pipeline.

Combines hay price history with supplemental signals (drought, diesel,
weather, production) into a model-ready DataFrame.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Any

import numpy as np
import pandas as pd


# ── Columns the model expects ─────────────────────────────────────────────────
FEATURE_COLS = [
    # Lag prices ($/ton)
    "price_lag1", "price_lag2", "price_lag4", "price_lag8", "price_lag12",
    # Rolling stats
    "roll4_mean", "roll4_std", "roll12_mean", "roll12_std",
    # Year-over-year
    "yoy_delta",
    # Seasonality (sine/cosine encoding of ISO week)
    "week_sin", "week_cos", "month_sin", "month_cos",
    # Drought
    "drought_d2_pct", "drought_d3_pct", "drought_d4_pct",
    # Diesel
    "diesel_price",
    # Weather (30-day rolling)
    "precip_30d", "tmax_30d",
]


def build_price_features(prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a weekly hay-price DataFrame with columns:
        report_date, price_wtavg
    (filtered for a single region/hay_type/grade segment),
    return the feature DataFrame aligned by date.
    """
    df = prices_df.copy()
    df = df.sort_values("report_date").set_index("report_date")
    price = df["price_wtavg"].astype(float)

    # Lag features
    df["price_lag1"] = price.shift(1)
    df["price_lag2"] = price.shift(2)
    df["price_lag4"] = price.shift(4)
    df["price_lag8"] = price.shift(8)
    df["price_lag12"] = price.shift(12)

    # Rolling statistics (window in weeks)
    df["roll4_mean"] = price.shift(1).rolling(4).mean()
    df["roll4_std"] = price.shift(1).rolling(4).std().fillna(0)
    df["roll12_mean"] = price.shift(1).rolling(12).mean()
    df["roll12_std"] = price.shift(1).rolling(12).std().fillna(0)

    # Year-over-year (52-week lag)
    df["yoy_delta"] = price - price.shift(52)

    # Seasonality encoding
    idx = pd.DatetimeIndex(df.index)
    df["week_sin"] = np.sin(2 * math.pi * idx.isocalendar().week.astype(float) / 52)
    df["week_cos"] = np.cos(2 * math.pi * idx.isocalendar().week.astype(float) / 52)
    df["month_sin"] = np.sin(2 * math.pi * idx.month / 12)
    df["month_cos"] = np.cos(2 * math.pi * idx.month / 12)

    return df


def merge_supplemental(
    features_df: pd.DataFrame,
    drought_df: pd.DataFrame | None = None,
    diesel_df: pd.DataFrame | None = None,
    weather_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Merge supplemental signals into the feature DataFrame.
    All supplemental frames must have a 'report_date' or 'observation_date' column.
    Missing supplemental data is forward-filled then filled with 0.
    """
    df = features_df.copy()

    if drought_df is not None and not drought_df.empty:
        d = drought_df.sort_values("report_date").set_index("report_date")
        d = d[["d2_pct", "d3_pct", "d4_pct"]].rename(
            columns={"d2_pct": "drought_d2_pct", "d3_pct": "drought_d3_pct", "d4_pct": "drought_d4_pct"}
        )
        df = df.join(d, how="left")
    else:
        df["drought_d2_pct"] = 0.0
        df["drought_d3_pct"] = 0.0
        df["drought_d4_pct"] = 0.0

    if diesel_df is not None and not diesel_df.empty:
        d = diesel_df.sort_values("report_date").set_index("report_date")
        d = d[["price_per_gallon"]].rename(columns={"price_per_gallon": "diesel_price"})
        df = df.join(d, how="left")
    else:
        df["diesel_price"] = 4.5  # fallback to a reasonable default

    if weather_df is not None and not weather_df.empty:
        # 30-day rolling aggregates from daily weather
        w = weather_df.sort_values("observation_date").set_index("observation_date")
        w = w[["precipitation_mm", "temp_max_c"]].astype(float)
        w_weekly = w.resample("W-MON").agg(
            precip_30d=("precipitation_mm", lambda x: x.rolling(30, min_periods=1).sum().iloc[-1] if len(x) else 0),
            tmax_30d=("temp_max_c", "mean"),
        )
        df = df.join(w_weekly, how="left")
    else:
        df["precip_30d"] = 10.0
        df["tmax_30d"] = 25.0

    # Forward-fill then zero-fill remaining NaN supplemental columns
    for col in ["drought_d2_pct", "drought_d3_pct", "drought_d4_pct",
                "diesel_price", "precip_30d", "tmax_30d"]:
        if col in df.columns:
            df[col] = df[col].ffill().fillna(0)

    return df


def prepare_training_data(
    features_df: pd.DataFrame,
    horizon_weeks: int = 1,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Shift the target by `horizon_weeks` to create a future-looking target.
    Drops rows with NaN in feature or target columns.
    """
    df = features_df.copy()
    df["target"] = df["price_wtavg"].shift(-horizon_weeks)

    # Keep only feature columns that exist
    available = [c for c in FEATURE_COLS if c in df.columns]
    df = df.dropna(subset=available + ["target"])

    X = df[available]
    y = df["target"]
    return X, y


def build_inference_row(
    last_prices: pd.Series,
    supplemental: dict[str, float],
    target_date: date,
) -> dict[str, float]:
    """
    Build a single feature row for inference from the last known price series
    and current supplemental signal values.
    """
    price_arr = last_prices.values.astype(float)

    def _lag(n: int) -> float:
        return float(price_arr[-n]) if len(price_arr) >= n else float(np.mean(price_arr))

    roll4 = price_arr[-4:] if len(price_arr) >= 4 else price_arr
    roll12 = price_arr[-12:] if len(price_arr) >= 12 else price_arr
    lag52 = price_arr[-52] if len(price_arr) >= 52 else price_arr[-1]

    import datetime
    iso = date.isocalendar(target_date)
    week_num = iso.week

    return {
        "price_lag1": _lag(1),
        "price_lag2": _lag(2),
        "price_lag4": _lag(4),
        "price_lag8": _lag(8),
        "price_lag12": _lag(12),
        "roll4_mean": float(np.mean(roll4)),
        "roll4_std": float(np.std(roll4)) if len(roll4) > 1 else 0.0,
        "roll12_mean": float(np.mean(roll12)),
        "roll12_std": float(np.std(roll12)) if len(roll12) > 1 else 0.0,
        "yoy_delta": float(price_arr[-1]) - float(lag52),
        "week_sin": math.sin(2 * math.pi * week_num / 52),
        "week_cos": math.cos(2 * math.pi * week_num / 52),
        "month_sin": math.sin(2 * math.pi * target_date.month / 12),
        "month_cos": math.cos(2 * math.pi * target_date.month / 12),
        "drought_d2_pct": supplemental.get("drought_d2_pct", 0.0),
        "drought_d3_pct": supplemental.get("drought_d3_pct", 0.0),
        "drought_d4_pct": supplemental.get("drought_d4_pct", 0.0),
        "diesel_price": supplemental.get("diesel_price", 4.5),
        "precip_30d": supplemental.get("precip_30d", 10.0),
        "tmax_30d": supplemental.get("tmax_30d", 25.0),
    }
