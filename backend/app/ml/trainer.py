"""
Training orchestrator — runs for all region/hay_type/grade/horizon combinations
using data from the database.
"""
from __future__ import annotations

import asyncio
import logging
from itertools import product

import pandas as pd
from sqlalchemy import select, text

from app.config import GRADES, HAY_TYPES, REGIONS
from app.database import AsyncSessionLocal
from app.ml.features import (
    build_price_features,
    merge_supplemental,
    prepare_training_data,
)
from app.ml.model import train_segment
from app.models import DroughtData, DieselPrice, HayPrice, WeatherData

logger = logging.getLogger(__name__)

HORIZONS = [1, 2, 4, 12]  # weeks ahead
MIN_SAMPLES = 52           # at least 1 year of weekly data


async def _load_price_series(
    session, region: str, hay_type: str, grade: str
) -> pd.DataFrame:
    result = await session.execute(
        select(HayPrice.report_date, HayPrice.price_wtavg)
        .where(
            HayPrice.region == region,
            HayPrice.hay_type == hay_type,
            HayPrice.grade == grade,
        )
        .order_by(HayPrice.report_date)
    )
    rows = result.fetchall()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows, columns=["report_date", "price_wtavg"])


async def _load_supplemental(session, region: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    drought = await session.execute(
        select(DroughtData.report_date, DroughtData.d2_pct, DroughtData.d3_pct, DroughtData.d4_pct)
        .where(DroughtData.region == region)
        .order_by(DroughtData.report_date)
    )
    drought_df = pd.DataFrame(drought.fetchall(), columns=["report_date", "d2_pct", "d3_pct", "d4_pct"])

    diesel = await session.execute(
        select(DieselPrice.report_date, DieselPrice.price_per_gallon)
        .order_by(DieselPrice.report_date)
    )
    diesel_df = pd.DataFrame(diesel.fetchall(), columns=["report_date", "price_per_gallon"])

    weather = await session.execute(
        select(WeatherData.observation_date, WeatherData.precipitation_mm, WeatherData.temp_max_c)
        .where(WeatherData.region == region)
        .order_by(WeatherData.observation_date)
    )
    weather_df = pd.DataFrame(weather.fetchall(), columns=["observation_date", "precipitation_mm", "temp_max_c"])

    return drought_df, diesel_df, weather_df


async def train_all() -> dict:
    """Train models for all segments and horizons. Returns a summary."""
    logger.info("Starting full model training run…")
    summary = {"trained": 0, "skipped": 0, "failed": 0}

    async with AsyncSessionLocal() as session:
        for region, hay_type, grade in product(REGIONS, HAY_TYPES, GRADES):
            prices_df = await _load_price_series(session, region, hay_type, grade)

            if prices_df.empty or len(prices_df) < MIN_SAMPLES:
                summary["skipped"] += 1
                continue

            drought_df, diesel_df, weather_df = await _load_supplemental(session, region)

            features_df = build_price_features(prices_df)
            features_df = merge_supplemental(features_df, drought_df, diesel_df, weather_df)
            # Keep price_wtavg in features_df so prepare_training_data can use it as target
            features_df["price_wtavg"] = prices_df.set_index("report_date")["price_wtavg"]

            segment_key = f"{region}/{hay_type}/{grade}"

            for horizon in HORIZONS:
                try:
                    X, y = prepare_training_data(features_df, horizon_weeks=horizon)
                    if len(X) < MIN_SAMPLES:
                        continue
                    train_segment(X, y, segment_key, horizon)
                    summary["trained"] += 1
                except Exception as exc:
                    logger.warning("Training failed for %s h=%d: %s", segment_key, horizon, exc)
                    summary["failed"] += 1

    logger.info("Training complete: %s", summary)
    return summary


async def retrain_if_needed() -> None:
    """Quick check — retrain only if new price data was recently added."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM hay_prices"))
            count = result.scalar()
            if count and count > 0:
                await train_all()
    except Exception as exc:
        logger.warning("Retraining skipped: %s", exc)
