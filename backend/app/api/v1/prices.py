from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import HayPrice
from app.schemas.hay_price import HayPriceOut, PriceSeriesPoint

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/", response_model=list[HayPriceOut])
async def list_prices(
    region: Optional[str] = Query(None),
    hay_type: Optional[str] = Query(None),
    grade: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(200, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List raw hay price records with optional filters."""
    q = select(HayPrice).order_by(HayPrice.report_date.desc())
    if region:
        q = q.where(HayPrice.region == region)
    if hay_type:
        q = q.where(HayPrice.hay_type == hay_type)
    if grade:
        q = q.where(HayPrice.grade == grade)
    if start_date:
        q = q.where(HayPrice.report_date >= start_date)
    if end_date:
        q = q.where(HayPrice.report_date <= end_date)
    q = q.limit(limit)

    result = await db.execute(q)
    return result.scalars().all()


@router.get("/series", response_model=list[PriceSeriesPoint])
async def price_series(
    region: str = Query(...),
    hay_type: str = Query(...),
    grade: str = Query(...),
    weeks: int = Query(104, ge=4, le=260),
    db: AsyncSession = Depends(get_db),
):
    """
    Return a weekly time series for a specific segment.
    Ideal for charting — ordered ascending by date.
    """
    start = date.today() - timedelta(weeks=weeks)
    result = await db.execute(
        select(HayPrice)
        .where(
            HayPrice.region == region,
            HayPrice.hay_type == hay_type,
            HayPrice.grade == grade,
            HayPrice.report_date >= start,
        )
        .order_by(HayPrice.report_date.asc())
    )
    rows = result.scalars().all()
    return [
        PriceSeriesPoint(
            report_date=r.report_date,
            price_wtavg=float(r.price_wtavg),
            price_low=float(r.price_low) if r.price_low else None,
            price_high=float(r.price_high) if r.price_high else None,
            volume_tons=r.volume_tons,
        )
        for r in rows
    ]


@router.get("/latest")
async def latest_prices(
    region: Optional[str] = Query(None),
    hay_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the most recent price for every region/hay_type/grade combination.
    Useful for the dashboard summary cards.
    """
    subq = (
        select(
            HayPrice.region,
            HayPrice.hay_type,
            HayPrice.grade,
            func.max(HayPrice.report_date).label("max_date"),
        )
        .group_by(HayPrice.region, HayPrice.hay_type, HayPrice.grade)
        .subquery()
    )

    q = select(HayPrice).join(
        subq,
        (HayPrice.region == subq.c.region)
        & (HayPrice.hay_type == subq.c.hay_type)
        & (HayPrice.grade == subq.c.grade)
        & (HayPrice.report_date == subq.c.max_date),
    )
    if region:
        q = q.where(HayPrice.region == region)
    if hay_type:
        q = q.where(HayPrice.hay_type == hay_type)

    result = await db.execute(q)
    rows = result.scalars().all()

    return [
        {
            "region": r.region,
            "hay_type": r.hay_type,
            "grade": r.grade,
            "report_date": r.report_date.isoformat(),
            "price_wtavg": float(r.price_wtavg),
            "price_low": float(r.price_low) if r.price_low else None,
            "price_high": float(r.price_high) if r.price_high else None,
        }
        for r in rows
    ]


@router.get("/summary")
async def price_summary(
    region: str = Query(...),
    hay_type: str = Query(...),
    grade: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Return current price + 4-week and 52-week comparison for a segment.
    """
    today = date.today()

    async def _price_on(target_date: date) -> Optional[float]:
        r = await db.execute(
            select(HayPrice.price_wtavg)
            .where(
                HayPrice.region == region,
                HayPrice.hay_type == hay_type,
                HayPrice.grade == grade,
                HayPrice.report_date <= target_date,
            )
            .order_by(HayPrice.report_date.desc())
            .limit(1)
        )
        val = r.scalar_one_or_none()
        return float(val) if val else None

    current = await _price_on(today)
    four_weeks_ago = await _price_on(today - timedelta(weeks=4))
    one_year_ago = await _price_on(today - timedelta(weeks=52))

    def _change(now, then):
        if now and then:
            return {"absolute": round(now - then, 2), "pct": round((now - then) / then * 100, 1)}
        return None

    return {
        "region": region,
        "hay_type": hay_type,
        "grade": grade,
        "current_price": current,
        "vs_4_weeks": _change(current, four_weeks_ago),
        "vs_1_year": _change(current, one_year_ago),
    }
