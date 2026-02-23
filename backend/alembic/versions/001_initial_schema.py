"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- hay_prices ---
    op.create_table(
        "hay_prices",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("report_date", sa.Date, nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("region", sa.String(50), nullable=False),
        sa.Column("hay_type", sa.String(50), nullable=False),
        sa.Column("grade", sa.String(50), nullable=True),
        sa.Column("price_low", sa.Numeric(10, 2), nullable=True),
        sa.Column("price_high", sa.Numeric(10, 2), nullable=True),
        sa.Column("price_wtavg", sa.Numeric(10, 2), nullable=False),
        sa.Column("volume_tons", sa.Integer, nullable=True),
        sa.Column("delivery_type", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_hay_prices_date_region", "hay_prices", ["report_date", "region"])
    op.create_index("ix_hay_prices_type", "hay_prices", ["hay_type", "grade"])

    # --- weather_data ---
    op.create_table(
        "weather_data",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("observation_date", sa.Date, nullable=False),
        sa.Column("station_id", sa.String(50), nullable=False),
        sa.Column("region", sa.String(50), nullable=False),
        sa.Column("precipitation_mm", sa.Numeric(8, 2), nullable=True),
        sa.Column("temp_max_c", sa.Numeric(6, 2), nullable=True),
        sa.Column("temp_min_c", sa.Numeric(6, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_weather_date_region", "weather_data", ["observation_date", "region"])

    # --- drought_data ---
    op.create_table(
        "drought_data",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("report_date", sa.Date, nullable=False),
        sa.Column("region", sa.String(50), nullable=False),
        sa.Column("d0_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("d1_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("d2_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("d3_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("d4_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_drought_date_region", "drought_data", ["report_date", "region"])

    # --- diesel_prices ---
    op.create_table(
        "diesel_prices",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("report_date", sa.Date, nullable=False),
        sa.Column("region", sa.String(50), nullable=False),
        sa.Column("price_per_gallon", sa.Numeric(8, 3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_diesel_date", "diesel_prices", ["report_date"])

    # --- hay_production ---
    op.create_table(
        "hay_production",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("report_date", sa.Date, nullable=False),
        sa.Column("region", sa.String(50), nullable=False),
        sa.Column("hay_type", sa.String(50), nullable=False),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit", sa.String(30), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_production_date_region", "hay_production", ["report_date", "region"])

    # --- forecasts ---
    op.create_table(
        "forecasts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("target_date", sa.Date, nullable=False),
        sa.Column("region", sa.String(50), nullable=False),
        sa.Column("hay_type", sa.String(50), nullable=False),
        sa.Column("grade", sa.String(50), nullable=False),
        sa.Column("horizon_weeks", sa.Integer, nullable=False),
        sa.Column("price_predicted", sa.Numeric(10, 2), nullable=False),
        sa.Column("price_low_80", sa.Numeric(10, 2), nullable=True),
        sa.Column("price_high_80", sa.Numeric(10, 2), nullable=True),
        sa.Column("price_low_95", sa.Numeric(10, 2), nullable=True),
        sa.Column("price_high_95", sa.Numeric(10, 2), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("feature_importance", postgresql.JSONB, nullable=True),
        sa.Column("mape_estimate", sa.Numeric(6, 4), nullable=True),
    )
    op.create_index("ix_forecasts_target", "forecasts", ["target_date", "region", "hay_type", "grade"])

    # --- alerts ---
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("region", sa.String(50), nullable=False),
        sa.Column("hay_type", sa.String(50), nullable=False),
        sa.Column("grade", sa.String(50), nullable=False),
        sa.Column("threshold_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),  # 'above' | 'below'
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- ingestion_logs ---
    op.create_table(
        "ingestion_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),  # success | failed | partial
        sa.Column("records_ingested", sa.Integer, default=0),
        sa.Column("error_message", sa.Text, nullable=True),
    )


def downgrade() -> None:
    for table in [
        "ingestion_logs", "alerts", "forecasts", "hay_production",
        "diesel_prices", "drought_data", "weather_data", "hay_prices"
    ]:
        op.drop_table(table)
