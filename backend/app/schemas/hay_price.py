from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class HayPriceFilter(BaseModel):
    region: Optional[str] = None
    hay_type: Optional[str] = None
    grade: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class HayPriceOut(BaseModel):
    id: int
    report_date: date
    source: str
    region: str
    hay_type: str
    grade: Optional[str]
    price_low: Optional[Decimal]
    price_high: Optional[Decimal]
    price_wtavg: Decimal
    volume_tons: Optional[int]
    delivery_type: Optional[str]

    model_config = {"from_attributes": True}


class PriceSeriesPoint(BaseModel):
    report_date: date
    price_wtavg: float
    price_low: Optional[float] = None
    price_high: Optional[float] = None
    volume_tons: Optional[int] = None
