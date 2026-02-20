"""
Inference service: generate forecasts for a given segment.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.ml.features import FEATURE_COLS, build_inference_row
from app.ml.model import load_meta, load_models, predict
from app.models import DroughtData, DieselPrice, HayPrice, WeatherData

logger = logging.getLogger(__name__)

HORIZONS = [1, 2, 4, 12]


async def generate_forecasts(
    session: AsyncSession,
    region: str,
    hay_type: str,
    grade: str,
) -> list[dict[str, Any]]:
    """
    Generate forecasts for all supported horizons for a given segment.
    Returns a list of forecast dicts ready to be stored in the DB.
    """
    segment_key = f"{region}/{hay_type}/{grade}"
    today = date.today()

    # Load recent price history (last 52 weeks)
    price_result = await session.execute(
        select(HayPrice.report_date, HayPrice.price_wtavg)
        .where(
            HayPrice.region == region,
            HayPrice.hay_type == hay_type,
            HayPrice.grade == grade,
            HayPrice.report_date >= today - timedelta(weeks=60),
        )
        .order_by(HayPrice.report_date)
    )
    prices = price_result.fetchall()

    if not prices or len(prices) < 4:
        logger.warning("Not enough price history for %s — skipping forecast", segment_key)
        return []

    prices_series = pd.Series(
        [float(p.price_wtavg) for p in prices],
        index=[p.report_date for p in prices],
    )

    # Load latest supplemental signals
    supplemental = await _get_latest_supplemental(session, region)

    forecasts: list[dict[str, Any]] = []

    for horizon in HORIZONS:
        models = load_models(segment_key, horizon)
        meta = load_meta(segment_key, horizon)

        if models is None or meta is None:
            logger.info("No trained model for %s h=%d — skipping", segment_key, horizon)
            continue

        target_date = today + timedelta(weeks=horizon)
        feature_row = build_inference_row(prices_series, supplemental, target_date)

        # Keep only features the model was trained on
        available = [c for c in FEATURE_COLS if c in meta.get("features", FEATURE_COLS)]
        X_row = pd.DataFrame([feature_row])[available]

        pred = predict(models, X_row)

        forecasts.append(
            {
                "target_date": target_date,
                "region": region,
                "hay_type": hay_type,
                "grade": grade,
                "horizon_weeks": horizon,
                "price_predicted": round(pred["price_predicted"], 2),
                "price_low_80": round(pred["price_low_80"], 2),
                "price_high_80": round(pred["price_high_80"], 2),
                "price_low_95": round(pred["price_low_95"], 2),
                "price_high_95": round(pred["price_high_95"], 2),
                "model_version": meta.get("model_version"),
                "feature_importance": meta.get("feature_importance"),
                "mape_estimate": round(meta.get("mape", 0.0), 4),
            }
        )

    return forecasts


async def _get_latest_supplemental(session: AsyncSession, region: str) -> dict[str, float]:
    """Pull the most recent supplemental signal values for a region."""
    signals: dict[str, float] = {}

    drought = await session.execute(
        select(DroughtData).where(DroughtData.region == region)
        .order_by(DroughtData.report_date.desc()).limit(1)
    )
    d = drought.scalar_one_or_none()
    if d:
        signals["drought_d2_pct"] = float(d.d2_pct or 0)
        signals["drought_d3_pct"] = float(d.d3_pct or 0)
        signals["drought_d4_pct"] = float(d.d4_pct or 0)

    diesel = await session.execute(
        select(DieselPrice).order_by(DieselPrice.report_date.desc()).limit(1)
    )
    dp = diesel.scalar_one_or_none()
    if dp:
        signals["diesel_price"] = float(dp.price_per_gallon)

    weather = await session.execute(
        select(WeatherData).where(WeatherData.region == region)
        .order_by(WeatherData.observation_date.desc()).limit(30)
    )
    rows = weather.scalars().all()
    if rows:
        precip = sum(float(r.precipitation_mm or 0) for r in rows)
        tmax_vals = [float(r.temp_max_c) for r in rows if r.temp_max_c is not None]
        signals["precip_30d"] = precip
        signals["tmax_30d"] = sum(tmax_vals) / len(tmax_vals) if tmax_vals else 25.0

    return signals
