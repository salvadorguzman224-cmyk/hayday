from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Alert
from app.schemas.alert import AlertCreate, AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/", response_model=AlertOut, status_code=201)
async def create_alert(payload: AlertCreate, db: AsyncSession = Depends(get_db)):
    """Create a price alert for a user."""
    if payload.direction not in ("above", "below"):
        raise HTTPException(422, "direction must be 'above' or 'below'")

    alert = Alert(**payload.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.get("/", response_model=list[AlertOut])
async def list_alerts(
    email: str = Query(..., description="User email"),
    db: AsyncSession = Depends(get_db),
):
    """List all alerts for a user email."""
    result = await db.execute(
        select(Alert)
        .where(Alert.user_email == email)
        .order_by(Alert.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/{alert_id}/toggle", response_model=AlertOut)
async def toggle_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """Toggle an alert active/inactive."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.is_active = not alert.is_active
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an alert."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(404, "Alert not found")
    await db.delete(alert)
    await db.commit()
