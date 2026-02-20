from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://hayday:hayday@db:5432/hayday"
    REDIS_URL: str = "redis://redis:6379"
    SECRET_KEY: str = "changeme"
    DEBUG: bool = True

    # External API keys (all free-tier)
    USDA_AMS_API_KEY: str = ""
    USDA_NASS_API_KEY: str = ""
    NOAA_API_KEY: str = ""
    EIA_API_KEY: str = ""

    # Alerts
    SENDGRID_API_KEY: str = ""
    ALERT_FROM_EMAIL: str = "alerts@hayprice.io"

    # ML
    MODEL_DIR: str = "/app/ml_models"

    class Config:
        env_file = ".env"


settings = Settings()

# ── Enumeration constants ─────────────────────────────────────────────────────

REGIONS = [
    "northern_ca",
    "sacramento_valley",
    "san_joaquin_valley",
    "southern_ca",
    "coastal_ca",
]

REGION_LABELS = {
    "northern_ca": "Northern California",
    "sacramento_valley": "Sacramento Valley",
    "san_joaquin_valley": "San Joaquin Valley",
    "southern_ca": "Southern CA / Desert",
    "coastal_ca": "Coastal California",
}

HAY_TYPES = ["alfalfa", "grass", "oat", "sudan", "mixed", "straw"]

GRADES = ["supreme", "premium", "good", "fair", "utility"]

SOURCES = ["usda_ams", "hoyt", "seed"]

DELIVERY_TYPES = ["fob", "delivered"]
