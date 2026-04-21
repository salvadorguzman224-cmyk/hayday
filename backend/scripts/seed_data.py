"""
Seed the database with synthetic but realistic California hay price data.

Covers 2020-01-06 through present at weekly intervals.
Prices follow documented seasonal patterns for each region/type/grade,
with realistic noise, drought effects (2020-2022 CA drought), and
post-pandemic diesel cost shocks.

Run:  python scripts/seed_data.py
"""
import asyncio
import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path

# Allow running from repo root or scripts/ dir
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://hayday:hayday@db:5432/hayday"
)

# ── Simulation parameters ─────────────────────────────────────────────────────

REGIONS = [
    "central_san_joaquin_valley",
    "north_intermountain",
    "north_san_joaquin_valley",
    "sacramento_valley",
    "southeast",
]

HAY_TYPES_GRADES: list[tuple[str, str]] = [
    ("alfalfa", "supreme"),
    ("alfalfa", "premium"),
    ("alfalfa", "good"),
    ("alfalfa", "fair"),
    ("grass", "premium"),
    ("grass", "good"),
    ("oat", "good"),
    ("mixed", "good"),
]

# Base prices ($/ton) by hay type and grade
BASE_PRICES: dict[tuple[str, str], float] = {
    ("alfalfa", "supreme"): 310,
    ("alfalfa", "premium"): 280,
    ("alfalfa", "good"): 240,
    ("alfalfa", "fair"): 200,
    ("grass", "premium"): 260,
    ("grass", "good"): 220,
    ("oat", "good"): 195,
    ("mixed", "good"): 210,
}

# Regional price adjustment (relative to base, $/ton)
REGION_ADJ: dict[str, float] = {
    "central_san_joaquin_valley":  0,    # biggest production area — base price
    "north_san_joaquin_valley":    5,    # dairy demand bumps it
    "sacramento_valley":          -5,    # production area, slightly cheaper
    "north_intermountain":        15,    # remote, transport cost
    "southeast":                  10,    # Imperial production + desert transport
}

# Seasonal amplitude (high in Jul-Sep = peak cutting/storage demand)
SEASONAL_AMP = 18.0

# Drought impact: d_severity (0-1) → price multiplier up to +20%
DROUGHT_MULTIPLIER = 0.20

# Diesel cost pass-through: $1 increase → +$8/ton delivered
DIESEL_PASSTHROUGH = 8.0

# Weekly noise std dev
NOISE_STD = 6.0


def _seasonal_component(week_of_year: int) -> float:
    """Sinusoidal seasonal: peak around week 32 (mid August)."""
    return SEASONAL_AMP * np.sin(2 * np.pi * (week_of_year - 8) / 52)


def _drought_severity(d: date) -> float:
    """
    Simulate CA drought severity 0-1.
    2020-2022: escalating drought (D3/D4 conditions peak in 2021).
    2023-2024: improving conditions (partial recovery).
    """
    if d.year < 2020:
        return 0.05
    if 2020 <= d.year < 2021:
        return 0.10 + 0.30 * ((d - date(2020, 1, 1)).days / 366)
    if d.year == 2021:
        return 0.40 + 0.20 * ((d - date(2021, 1, 1)).days / 365)
    if d.year == 2022:
        return max(0.0, 0.60 - 0.25 * ((d - date(2022, 1, 1)).days / 365))
    if d.year == 2023:
        return max(0.0, 0.35 - 0.30 * ((d - date(2023, 1, 1)).days / 365))
    return 0.05 + np.random.uniform(0, 0.10)


def _diesel_price(d: date) -> float:
    """
    Simulate weekly CA diesel price ($/gallon).
    2020: low (~$3.20), 2022: spike (~$6.50), 2023-2024: ~$4.80-5.20
    """
    if d < date(2021, 1, 1):
        return 3.20 + np.random.normal(0, 0.08)
    if d < date(2022, 3, 1):
        return 3.80 + np.random.normal(0, 0.10)
    if d < date(2022, 9, 1):
        t = (d - date(2022, 3, 1)).days / 180
        return 3.80 + t * 2.70 + np.random.normal(0, 0.15)
    if d < date(2023, 3, 1):
        t = (d - date(2022, 9, 1)).days / 180
        return 6.50 - t * 1.80 + np.random.normal(0, 0.12)
    return 4.80 + np.random.normal(0, 0.10)


async def seed(session: AsyncSession) -> None:
    # Check if already seeded
    result = await session.execute(text("SELECT COUNT(*) FROM hay_prices WHERE source='seed'"))
    existing = result.scalar()
    if existing and existing > 100:
        logger.info("Database already seeded (%d seed records) — skipping", existing)
        return

    logger.info("Seeding hay price data…")

    rng = np.random.default_rng(42)
    start = date(2020, 1, 6)
    end = date.today()

    weeks: list[date] = []
    d = start
    while d <= end:
        weeks.append(d)
        d += timedelta(weeks=1)

    hay_rows: list[dict] = []
    drought_rows: list[dict] = []
    diesel_rows: list[dict] = []

    prev_prices: dict[tuple, float] = {}

    for week_date in weeks:
        week_of_year = week_date.isocalendar()[1]
        drought = _drought_severity(week_date)
        diesel = max(2.5, _diesel_price(week_date))

        # Diesel price record (California-wide)
        diesel_rows.append(
            {"report_date": week_date, "region": "california", "price_per_gallon": round(diesel, 3)}
        )

        for region in REGIONS:
            for hay_type, grade in HAY_TYPES_GRADES:
                key = (region, hay_type, grade)
                base = BASE_PRICES[(hay_type, grade)] + REGION_ADJ[region]

                # Start from last week's price or base (mean-reverting AR(1))
                last = prev_prices.get(key, base)
                ar_pull = 0.15 * (base - last)

                seasonal = _seasonal_component(week_of_year)
                drought_effect = DROUGHT_MULTIPLIER * drought * base
                diesel_effect = DIESEL_PASSTHROUGH * max(0, diesel - 3.0)
                noise = rng.normal(0, NOISE_STD)

                price_wtavg = last + ar_pull + seasonal * 0.25 + drought_effect * 0.05 + diesel_effect * 0.05 + noise
                price_wtavg = max(80.0, round(price_wtavg, 2))
                spread = rng.uniform(8, 25)
                price_low = round(price_wtavg - spread / 2, 2)
                price_high = round(price_wtavg + spread / 2, 2)

                prev_prices[key] = price_wtavg

                volume = int(rng.integers(50, 800))

                hay_rows.append(
                    {
                        "report_date": week_date,
                        "source": "seed",
                        "region": region,
                        "hay_type": hay_type,
                        "grade": grade,
                        "price_low": price_low,
                        "price_high": price_high,
                        "price_wtavg": price_wtavg,
                        "volume_tons": volume,
                        "delivery_type": "fob",
                    }
                )

            # Drought data per region per week
            drought_rows.append(
                {
                    "report_date": week_date,
                    "region": region,
                    "d0_pct": round(min(100, drought * 80 + rng.uniform(-5, 5)), 2),
                    "d1_pct": round(min(100, drought * 60 + rng.uniform(-5, 5)), 2),
                    "d2_pct": round(min(100, drought * 40 + rng.uniform(-5, 5)), 2),
                    "d3_pct": round(min(100, drought * 20 + rng.uniform(-3, 3)), 2),
                    "d4_pct": round(min(100, max(0, drought * 8 + rng.uniform(-2, 2))), 2),
                }
            )

    # Bulk insert
    logger.info("Inserting %d hay price records…", len(hay_rows))
    await session.execute(
        text(
            "INSERT INTO hay_prices "
            "(report_date, source, region, hay_type, grade, price_low, price_high, "
            "price_wtavg, volume_tons, delivery_type) VALUES "
            "(:report_date, :source, :region, :hay_type, :grade, :price_low, :price_high, "
            ":price_wtavg, :volume_tons, :delivery_type)"
        ),
        hay_rows,
    )

    logger.info("Inserting %d drought records…", len(drought_rows))
    await session.execute(
        text(
            "INSERT INTO drought_data "
            "(report_date, region, d0_pct, d1_pct, d2_pct, d3_pct, d4_pct) VALUES "
            "(:report_date, :region, :d0_pct, :d1_pct, :d2_pct, :d3_pct, :d4_pct)"
        ),
        drought_rows,
    )

    logger.info("Inserting %d diesel price records…", len(diesel_rows))
    await session.execute(
        text(
            "INSERT INTO diesel_prices (report_date, region, price_per_gallon) VALUES "
            "(:report_date, :region, :price_per_gallon)"
        ),
        diesel_rows,
    )

    await session.commit()
    logger.info("Seed complete: %d hay prices, %d drought, %d diesel",
                len(hay_rows), len(drought_rows), len(diesel_rows))


async def main() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
