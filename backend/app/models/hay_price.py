from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class HayPrice(Base):
    __tablename__ = "hay_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    hay_type: Mapped[str] = mapped_column(String(50), nullable=False)
    grade: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    price_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    price_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    price_wtavg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    volume_tons: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    delivery_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return (
            f"<HayPrice {self.report_date} {self.region} {self.hay_type} "
            f"{self.grade} ${self.price_wtavg}>"
        )
