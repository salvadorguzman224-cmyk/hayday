from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.ml.predictor import generate_forecasts
from app.models import Forecast
from app.schemas.forecast import ForecastOut

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.get("/", response_model=list[ForecastOut])
async def get_forecasts(
    region: str = Query(...),
    hay_type: str = Query(...),
    grade: str = Query(...),
    horizon_weeks: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the latest stored forecasts for a segment.
    If none exist, generate them on-the-fly (first call may take a moment).
    """
    q = (
        select(Forecast)
        .where(
            Forecast.region == region,
            Forecast.hay_type == hay_type,
            Forecast.grade == grade,
        )
        .order_by(Forecast.generated_at.desc(), Forecast.horizon_weeks.asc())
        .limit(20)
    )
    if horizon_weeks:
        q = q.where(Forecast.horizon_weeks == horizon_weeks)

    result = await db.execute(q)
    rows = result.scalars().all()

    if not rows:
        # Generate on-demand
        rows = await _generate_and_store(db, region, hay_type, grade)

    return rows


@router.post("/refresh")
async def refresh_forecasts(
    region: str = Query(...),
    hay_type: str = Query(...),
    grade: str = Query(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """Trigger a fresh forecast generation for a segment."""
    rows = await _generate_and_store(db, region, hay_type, grade)
    return {"message": f"Generated {len(rows)} forecasts", "forecasts": len(rows)}


async def _generate_and_store(
    db: AsyncSession, region: str, hay_type: str, grade: str
) -> list[Forecast]:
    forecasts_data = await generate_forecasts(db, region, hay_type, grade)
    if not forecasts_data:
        return []

    # Remove old forecasts for this segment
    await db.execute(
        delete(Forecast).where(
            Forecast.region == region,
            Forecast.hay_type == hay_type,
            Forecast.grade == grade,
        )
    )

    new_rows = []
    for f in forecasts_data:
        obj = Forecast(**f)
        db.add(obj)
        new_rows.append(obj)

    await db.commit()
    for obj in new_rows:
        await db.refresh(obj)

    return new_rows


@router.get("/dashboard")
async def dashboard_forecasts(
    region: str = Query(...),
    hay_type: str = Query("alfalfa"),
    grade: str = Query("premium"),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns 1-week and 4-week forecasts bundled for the dashboard summary card.
    """
    result = await db.execute(
        select(Forecast)
        .where(
            Forecast.region == region,
            Forecast.hay_type == hay_type,
            Forecast.grade == grade,
            Forecast.horizon_weeks.in_([1, 4]),
        )
        .order_by(Forecast.generated_at.desc())
        .limit(4)
    )
    rows = result.scalars().all()

    out: dict = {}
    for row in rows:
        key = f"h{row.horizon_weeks}"
        out[key] = {
            "target_date": row.target_date.isoformat(),
            "price_predicted": float(row.price_predicted),
            "price_low_80": float(row.price_low_80) if row.price_low_80 else None,
            "price_high_80": float(row.price_high_80) if row.price_high_80 else None,
            "mape_estimate": float(row.mape_estimate) if row.mape_estimate else None,
            "feature_importance": row.feature_importance,
        }

    return out
