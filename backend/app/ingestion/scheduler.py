"""
APScheduler job definitions for automated data ingestion.

Schedule:
  - Wednesday 14:00 UTC  → USDA AMS hay prices
  - Monday    08:00 UTC  → U.S. Drought Monitor
  - Friday    16:00 UTC  → EIA diesel prices
  - 1st of month 06:00  → NOAA weather + USDA NASS production
  - After each successful ingestion → trigger model retraining
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, text

from app.database import AsyncSessionLocal
from app.ingestion.drought_monitor import DroughtMonitorClient
from app.ingestion.eia import EIAClient
from app.ingestion.noaa import NOAAClient
from app.ingestion.usda_ams import USDAamsClient
from app.ingestion.usda_nass import USDANassClient
from app.models import DroughtData, DieselPrice, HayPrice, HayProduction, IngestionLog, WeatherData
from app.config import REGIONS

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="UTC")


async def _log_ingestion(source: str, status: str, records: int, error: str | None = None) -> None:
    async with AsyncSessionLocal() as session:
        log = IngestionLog(
            source=source,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            status=status,
            records_ingested=records,
            error_message=error,
        )
        session.add(log)
        await session.commit()


async def ingest_usda_ams() -> None:
    logger.info("Ingesting USDA AMS California Direct Hay Report…")
    client = USDAamsClient()
    try:
        records = await client.fetch_latest()
        if not records:
            await _log_ingestion("usda_ams", "partial", 0, "No records returned")
            return

        async with AsyncSessionLocal() as session:
            for r in records:
                # Skip duplicates by date+region+type+grade
                existing = await session.execute(
                    select(HayPrice).where(
                        HayPrice.report_date == r["report_date"],
                        HayPrice.source == r["source"],
                        HayPrice.region == r["region"],
                        HayPrice.hay_type == r["hay_type"],
                        HayPrice.grade == r.get("grade"),
                    )
                )
                if existing.scalar_one_or_none() is None:
                    session.add(HayPrice(**r))
            await session.commit()

        await _log_ingestion("usda_ams", "success", len(records))
        logger.info("USDA AMS ingestion complete: %d records", len(records))

        # Trigger async retraining
        from app.ml.trainer import retrain_if_needed
        await retrain_if_needed()

    except Exception as exc:
        logger.exception("USDA AMS ingestion failed")
        await _log_ingestion("usda_ams", "failed", 0, str(exc))


async def ingest_drought_monitor() -> None:
    logger.info("Ingesting U.S. Drought Monitor data…")
    client = DroughtMonitorClient()
    today = date.today()
    # Drought Monitor reports are published on Tuesdays — use last Tuesday
    days_back = (today.weekday() - 1) % 7
    report_date = today - timedelta(days=days_back)

    try:
        records = await client.fetch_for_date(report_date)
        async with AsyncSessionLocal() as session:
            for r in records:
                existing = await session.execute(
                    select(DroughtData).where(
                        DroughtData.report_date == r["report_date"],
                        DroughtData.region == r["region"],
                    )
                )
                if existing.scalar_one_or_none() is None:
                    session.add(DroughtData(**r))
            await session.commit()

        await _log_ingestion("drought_monitor", "success", len(records))
    except Exception as exc:
        logger.exception("Drought Monitor ingestion failed")
        await _log_ingestion("drought_monitor", "failed", 0, str(exc))


async def ingest_eia_diesel() -> None:
    logger.info("Ingesting EIA diesel prices…")
    client = EIAClient()
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    try:
        records = await client.fetch_diesel_prices(start_date, end_date)
        async with AsyncSessionLocal() as session:
            for r in records:
                existing = await session.execute(
                    select(DieselPrice).where(
                        DieselPrice.report_date == r["report_date"],
                        DieselPrice.region == r["region"],
                    )
                )
                if existing.scalar_one_or_none() is None:
                    session.add(DieselPrice(**r))
            await session.commit()

        await _log_ingestion("eia", "success", len(records))
    except Exception as exc:
        logger.exception("EIA ingestion failed")
        await _log_ingestion("eia", "failed", 0, str(exc))


async def ingest_noaa_weather() -> None:
    logger.info("Ingesting NOAA weather data…")
    client = NOAAClient()
    end_date = date.today()
    start_date = end_date - timedelta(days=35)

    total = 0
    try:
        async with AsyncSessionLocal() as session:
            for region in REGIONS:
                records = await client.fetch_weather(region, start_date, end_date)
                for r in records:
                    existing = await session.execute(
                        select(WeatherData).where(
                            WeatherData.observation_date == r["observation_date"],
                            WeatherData.region == r["region"],
                        )
                    )
                    if existing.scalar_one_or_none() is None:
                        session.add(WeatherData(**r))
                total += len(records)
            await session.commit()

        await _log_ingestion("noaa", "success", total)
    except Exception as exc:
        logger.exception("NOAA ingestion failed")
        await _log_ingestion("noaa", "failed", 0, str(exc))


async def ingest_nass_production() -> None:
    logger.info("Ingesting USDA NASS production data…")
    client = USDANassClient()
    current_year = date.today().year

    total = 0
    try:
        async with AsyncSessionLocal() as session:
            for year in [current_year - 1, current_year]:
                records = await client.fetch_production(year)
                for r in records:
                    session.add(HayProduction(**r))
                    total += 1
            await session.commit()

        await _log_ingestion("usda_nass", "success", total)
    except Exception as exc:
        logger.exception("USDA NASS ingestion failed")
        await _log_ingestion("usda_nass", "failed", 0, str(exc))


def start_scheduler() -> None:
    scheduler.add_job(ingest_usda_ams, "cron", day_of_week="wed", hour=14, minute=0)
    scheduler.add_job(ingest_drought_monitor, "cron", day_of_week="mon", hour=8, minute=0)
    scheduler.add_job(ingest_eia_diesel, "cron", day_of_week="fri", hour=16, minute=0)
    scheduler.add_job(ingest_noaa_weather, "cron", day=1, hour=6, minute=0)
    scheduler.add_job(ingest_nass_production, "cron", day=1, hour=7, minute=0)
    scheduler.start()
    logger.info("Ingestion scheduler started")
