from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import IngestionLog

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.get("/logs")
async def ingestion_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Return recent ingestion audit log entries."""
    result = await db.execute(
        select(IngestionLog).order_by(IngestionLog.started_at.desc()).limit(limit)
    )
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "source": r.source,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "status": r.status,
            "records_ingested": r.records_ingested,
            "error_message": r.error_message,
        }
        for r in rows
    ]


@router.post("/trigger/{source}")
async def trigger_ingestion(source: str, background_tasks: BackgroundTasks):
    """Manually trigger ingestion for a specific source."""
    from app.ingestion.scheduler import (
        ingest_usda_ams,
        ingest_drought_monitor,
        ingest_eia_diesel,
        ingest_noaa_weather,
        ingest_nass_production,
    )

    handlers = {
        "usda_ams": ingest_usda_ams,
        "drought_monitor": ingest_drought_monitor,
        "eia": ingest_eia_diesel,
        "noaa": ingest_noaa_weather,
        "usda_nass": ingest_nass_production,
    }

    if source not in handlers:
        return {"error": f"Unknown source '{source}'. Valid: {list(handlers)}"}

    background_tasks.add_task(handlers[source])
    return {"message": f"Ingestion for '{source}' triggered in background"}


@router.post("/retrain")
async def trigger_retrain(background_tasks: BackgroundTasks):
    """Manually trigger model retraining."""
    from app.ml.trainer import train_all
    background_tasks.add_task(train_all)
    return {"message": "Model retraining triggered in background"}
