# Hay Price Predictor

An AI-powered platform for forecasting California hay commodity prices using USDA market reports, drought data, diesel prices, and machine learning.

## Architecture

```
frontend/   → Next.js 14 dashboard (React + Recharts + Tailwind)
backend/    → FastAPI + SQLAlchemy + XGBoost prediction engine
```

### Data Sources
| Source | Data | Frequency |
|--------|------|-----------|
| USDA AMS (`LM_GR212`) | CA Direct Hay Prices | Weekly |
| Hoyt Report | Regional market commentary | Weekly |
| NOAA CDO | Precipitation, temperature | Monthly |
| USDA NASS | Hay production + stocks | Quarterly |
| EIA | CA diesel fuel prices | Weekly |
| U.S. Drought Monitor | Drought severity by region | Weekly |

## Quick Start

### 1. Prerequisites
- Docker + Docker Compose
- (Optional) Free API keys for live data ingestion

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — add API keys for live data (platform works without them using seed data)
```

### 3. Run everything

```bash
docker-compose up --build
```

This will:
1. Start PostgreSQL (TimescaleDB) + Redis
2. Run Alembic database migrations
3. Seed the database with 5 years of realistic synthetic CA hay price data
4. Train XGBoost forecast models for all region/hay_type/grade combinations
5. Start the FastAPI backend on **http://localhost:8000**
6. Start the Next.js frontend on **http://localhost:3000**

### 4. Access the platform

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |
| API docs (ReDoc) | http://localhost:8000/redoc |

## Free API Key Registration

| API | Register At |
|-----|------------|
| USDA AMS Market News | https://mymarketnews.ams.usda.gov |
| USDA NASS Quick Stats | https://quickstats.nass.usda.gov |
| NOAA Climate Data | https://www.ncdc.noaa.gov/cdo-web |
| EIA Open Data | https://www.eia.gov/opendata |

All APIs are free with registration.

## Key API Endpoints

```
GET  /api/v1/prices/series?region=central_san_joaquin_valley&hay_type=alfalfa&grade=premium
GET  /api/v1/prices/latest?region=central_san_joaquin_valley
GET  /api/v1/prices/summary?region=central_san_joaquin_valley&hay_type=alfalfa&grade=premium
GET  /api/v1/forecasts/?region=central_san_joaquin_valley&hay_type=alfalfa&grade=premium
POST /api/v1/forecasts/refresh?region=...&hay_type=...&grade=...
POST /api/v1/alerts/
GET  /api/v1/alerts/?email=user@example.com
POST /api/v1/ingestion/trigger/{source}
POST /api/v1/ingestion/retrain
GET  /api/v1/ingestion/logs
GET  /api/v1/meta
```

## ML Model

- **Algorithm:** XGBoost with quantile regression (q2.5, q10, q50, q90, q97.5)
- **Horizons:** 1, 2, 4, and 12 weeks ahead
- **Segments:** 5 regions × 8 hay type/grade combos = 40 segments × 4 horizons = 160 models
- **Features:** Price lags, rolling averages, drought severity, diesel price, weather, seasonal encoding
- **Target MAPE:** ≤ 8% on 4-week horizon

### Retrain manually
```bash
docker-compose exec backend python scripts/train_model.py
```

### Trigger live data ingestion
```bash
# Via API
curl -X POST http://localhost:8000/api/v1/ingestion/trigger/usda_ams
curl -X POST http://localhost:8000/api/v1/ingestion/trigger/eia
curl -X POST http://localhost:8000/api/v1/ingestion/trigger/drought_monitor
```

## Automated Ingestion Schedule

| Source | Day | Time (UTC) |
|--------|-----|-----------|
| USDA AMS | Wednesday | 14:00 |
| Drought Monitor | Monday | 08:00 |
| EIA Diesel | Friday | 16:00 |
| NOAA Weather | 1st of month | 06:00 |
| USDA NASS | 1st of month | 07:00 |

## Regions

| ID | Label | Counties |
|----|-------|----------|
| `central_san_joaquin_valley` | Central San Joaquin Valley | Fresno, Madera, Kings, Tulare, Merced, Kern |
| `north_intermountain` | North Inter-Mountain | Modoc, Lassen, Siskiyou, Plumas, Shasta |
| `north_san_joaquin_valley` | North San Joaquin Valley | San Joaquin, Stanislaus |
| `sacramento_valley` | Sacramento Valley | Sacramento, Yolo, Sutter, Yuba, Colusa, Butte, Glenn, Tehama |
| `southeast` | Southeast California | Imperial, Riverside, San Bernardino, Inyo |

## Development

```bash
# Backend only (requires local PostgreSQL)
cd backend
pip install -r requirements.txt
DATABASE_URL=postgresql+asyncpg://... uvicorn app.main:app --reload

# Frontend only (requires backend running)
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```
