from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel


class ForecastRequest(BaseModel):
    region: str
    hay_type: str
    grade: str


class ForecastOut(BaseModel):
    id: int
    generated_at: datetime
    target_date: date
    region: str
    hay_type: str
    grade: str
    horizon_weeks: int
    price_predicted: Decimal
    price_low_80: Optional[Decimal]
    price_high_80: Optional[Decimal]
    price_low_95: Optional[Decimal]
    price_high_95: Optional[Decimal]
    model_version: Optional[str]
    feature_importance: Optional[dict[str, Any]]
    mape_estimate: Optional[Decimal]

    model_config = {"from_attributes": True}
