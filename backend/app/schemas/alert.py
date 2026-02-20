from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr


class AlertCreate(BaseModel):
    user_email: str
    region: str
    hay_type: str
    grade: str
    threshold_price: Decimal
    direction: str  # 'above' | 'below'


class AlertOut(BaseModel):
    id: int
    user_email: str
    region: str
    hay_type: str
    grade: str
    threshold_price: Decimal
    direction: str
    is_active: bool
    created_at: datetime
    last_triggered_at: Optional[datetime]

    model_config = {"from_attributes": True}
