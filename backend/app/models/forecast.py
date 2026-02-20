from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    hay_type: Mapped[str] = mapped_column(String(50), nullable=False)
    grade: Mapped[str] = mapped_column(String(50), nullable=False)
    horizon_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    price_predicted: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_low_80: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    price_high_80: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    price_low_95: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    price_high_95: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    feature_importance: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    mape_estimate: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
