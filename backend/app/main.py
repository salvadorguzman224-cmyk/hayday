import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.prices import router as prices_router
from app.api.v1.forecasts import router as forecasts_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.ingestion import router as ingestion_router
from app.config import settings
from app.ingestion.scheduler import start_scheduler

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

app = FastAPI(
    title="Hay Price Predictor API",
    version="1.0.0",
    description="Forecast and historical analytics for California hay markets",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(prices_router, prefix="/api/v1")
app.include_router(forecasts_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(ingestion_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event() -> None:
    start_scheduler()


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/v1/meta")
async def meta():
    """Return available filter options for the UI."""
    from app.config import REGIONS, HAY_TYPES, GRADES, REGION_LABELS
    return {
        "regions": [{"value": r, "label": REGION_LABELS[r]} for r in REGIONS],
        "hay_types": HAY_TYPES,
        "grades": GRADES,
    }
