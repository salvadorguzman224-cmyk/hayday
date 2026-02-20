from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WeatherData(Base):
    __tablename__ = "weather_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)
    station_id: Mapped[str] = mapped_column(String(50), nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    precipitation_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    temp_max_c: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    temp_min_c: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DroughtData(Base):
    __tablename__ = "drought_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    d0_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    d1_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    d2_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    d3_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    d4_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DieselPrice(Base):
    __tablename__ = "diesel_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    price_per_gallon: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HayProduction(Base):
    __tablename__ = "hay_production"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    hay_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
