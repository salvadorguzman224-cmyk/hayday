# Product Requirements Document
## Hay Price Predictor Platform

**Version:** 1.0
**Date:** February 20, 2026
**Status:** Draft

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Goals and Objectives](#goals-and-objectives)
4. [Target Users](#target-users)
5. [Data Sources](#data-sources)
6. [Features and Requirements](#features-and-requirements)
7. [Technical Architecture](#technical-architecture)
8. [API Integrations](#api-integrations)
9. [Machine Learning Model](#machine-learning-model)
10. [User Interface](#user-interface)
11. [Non-Functional Requirements](#non-functional-requirements)
12. [Success Metrics](#success-metrics)
13. [Phased Rollout](#phased-rollout)
14. [Risks and Mitigations](#risks-and-mitigations)
15. [Open Questions](#open-questions)

---

## 1. Executive Summary

The Hay Price Predictor is a data-driven web platform that forecasts hay commodity prices by region—with an initial focus on California. It ingests structured market reports (USDA California Direct Hay Report, Hoyt Report) and supplemental economic and environmental signals to train and serve a machine-learning prediction model. Users—farmers, feed dealers, livestock operators, and commodity brokers—receive short- and medium-term price forecasts alongside historical trend analytics to make informed buying and selling decisions.

---

## 2. Problem Statement

Hay is a multi-billion-dollar commodity in the U.S. West, yet pricing remains opaque and volatile. Buyers and sellers currently rely on:

- Weekly USDA paper/PDF market reports that require manual interpretation
- Anecdotal knowledge of local market conditions
- Lagging indicators such as last week's auction prices

This creates asymmetric information: large commercial buyers with dedicated analysts have a decisive edge over small farms and independent dealers. There is no unified, real-time platform that aggregates authoritative data, identifies pricing trends, and surfaces actionable forecasts.

---

## 3. Goals and Objectives

| Goal | Objective | Measurable Target |
|------|-----------|-------------------|
| Accurate price forecasting | Predict weekly hay prices per region/grade | Mean Absolute Percentage Error (MAPE) ≤ 8% within 4-week horizon |
| Data consolidation | Aggregate all major public hay market data sources | ≥ 3 primary data feeds live at launch |
| Accessibility | Provide forecasts to small operators, not just large buyers | Mobile-responsive UI; no subscription required for basic tier |
| Timeliness | Reflect latest market movements | Data refreshed within 24 hours of new report publication |
| Transparency | Explain what drives each forecast | Feature importance visible per prediction |

---

## 4. Target Users

### 4.1 Primary Users

| User Type | Description | Key Need |
|-----------|-------------|----------|
| **Hay Farmers / Growers** | Produce and sell hay in California and surrounding states | Know when to sell, what price to expect |
| **Livestock Operators** | Ranchers who purchase hay to feed cattle, horses, dairy | Forecast feed cost to manage budgets |
| **Feed Dealers / Brokers** | Intermediaries who buy and re-sell hay | Spot arbitrage opportunities; manage inventory risk |
| **Dairy Operations** | Large buyers of alfalfa and grass hay | Lock in forward contracts at favorable moments |

### 4.2 Secondary Users

| User Type | Description |
|-----------|-------------|
| **Agricultural Lenders** | Use price forecasts in loan underwriting |
| **Commodity Analysts** | Research and reporting on western hay markets |
| **Extension Agents** | Advise farmers on market timing |

---

## 5. Data Sources

### 5.1 Primary Data Sources

#### 5.1.1 USDA AMS — California Direct Hay Report

- **Source:** USDA Agricultural Marketing Service (AMS) Market News
- **Report ID:** `LM_GR212` (California Direct Hay — Weekly)
- **Access:** USDA AMS Market News API (`marsapi.ams.usda.gov`)
- **Endpoint:** `GET /services/v1.2/reports/{slug_id}`
- **Authentication:** API key (free registration at `mymarketnews.ams.usda.gov`)
- **Frequency:** Weekly (published every Wednesday)
- **Data Fields Captured:**
  - Report date
  - Commodity (Alfalfa, Grass, Oat, Sudan, Mixed, Straw)
  - Grade (Premium, Supreme, Good, Fair, Utility)
  - Region within California (Northern, Central, Southern)
  - Price range (low, high, weighted average) in $/ton
  - Volume (tons traded)
  - Delivery type (FOB, Delivered)

#### 5.1.2 Hoyt Report

- **Source:** Hoyt Hay Market Report (independent regional market newsletter published by Hoyt Hay Brokers)
- **Access Method:** Structured PDF/email digest — scraped or parsed via PDF extraction pipeline; investigate whether an API or structured feed is available
- **Frequency:** Weekly
- **Data Fields Captured:**
  - Regional hay prices (inland, coastal, desert markets)
  - Hay type and grade breakdown
  - Qualitative market commentary (processed via NLP to extract directional sentiment)
  - Supply/demand annotations

> **Note:** Direct API access for the Hoyt Report is TBD. An ETL pipeline using PDF parsing (e.g., `pdfplumber`, `pypdf`) or email ingestion will be implemented if no structured feed exists.

### 5.2 Supplemental Data Sources (Price Influencers)

| Data Source | Signal | Frequency | Access |
|-------------|--------|-----------|--------|
| **NOAA Climate Data Online** | Precipitation, temperature anomaly, drought index (PDSI) | Monthly/Weekly | NOAA CDO API (free) |
| **USDA NASS — Hay Stocks** | National/regional hay stocks and production forecasts | Quarterly | NASS API (free) |
| **USDA NASS — Crop Progress** | Alfalfa cutting progress, condition ratings | Weekly (growing season) | NASS API (free) |
| **U.S. Drought Monitor** | Drought severity by county/region | Weekly | Drought Monitor API (free) |
| **EIA — Diesel Fuel Prices** | Transportation cost proxy (affects delivered price) | Weekly | EIA Open Data API (free) |
| **CME Futures — Rough Rice / Corn / Soybean** | Feed commodity correlation signals | Daily | CME / Quandl / Alpha Vantage |
| **CPI — Animal Feeds** | Inflation in feed sector | Monthly | BLS API (free) |
| **California Water Board — Irrigation Data** | Water availability for alfalfa production | Monthly | CA Open Data Portal |
| **Export Data (USDA FAS)** | Hay export volumes (especially compressed alfalfa to Asia) | Monthly | USDA FAS API (free) |

---

## 6. Features and Requirements

### 6.1 Core Features

#### F-001: Regional Price Dashboard
- Display current and historical hay prices by region (California: Northern, Central, Southern, Desert)
- Filter by hay type (Alfalfa, Grass, Oat, Mixed, Straw) and grade (Supreme, Premium, Good, Fair, Utility)
- Interactive time-series chart with configurable date range
- Show price spread (low / high / weighted average)

#### F-002: Price Forecast Engine
- Generate short-term (1–4 week) and medium-term (1–3 month) price forecasts per region and hay type
- Display confidence intervals (80% and 95%)
- Highlight key drivers influencing the forecast (feature importance panel)
- Refresh forecast automatically after each new data ingestion cycle

#### F-003: Data Ingestion Pipeline
- Automated ingestion from all configured data sources on their respective schedules
- Data validation, deduplication, and anomaly flagging
- Ingestion audit log (what was pulled, when, how many records)
- Alerting on ingestion failure (email / Slack webhook)

#### F-004: Alert System
- Users can set price threshold alerts (e.g., "notify me when Premium Alfalfa in Central CA drops below $280/ton")
- Email and in-app notification delivery
- Alert history log

#### F-005: Historical Data Explorer
- Full searchable archive of all ingested report data
- Export to CSV / Excel
- Annotated timeline showing exogenous events (drought declarations, export surges, etc.)

#### F-006: Market Commentary Feed
- Aggregated qualitative commentary from ingested reports (Hoyt Report NLP extraction)
- Sentiment trend over time (bullish / neutral / bearish)

#### F-007: API Access (Developer / Power User Tier)
- REST API endpoints for forecast data, historical prices, and ingestion status
- API key management in user dashboard
- Rate limiting and usage tracking

### 6.2 Feature Priority

| Feature | Priority | Phase |
|---------|----------|-------|
| Data Ingestion Pipeline | P0 | 1 |
| Regional Price Dashboard | P0 | 1 |
| Price Forecast Engine | P0 | 2 |
| Alert System | P1 | 2 |
| Historical Data Explorer | P1 | 2 |
| Market Commentary Feed | P2 | 3 |
| API Access | P2 | 3 |

---

## 7. Technical Architecture

### 7.1 System Overview

```
┌──────────────────────────────────────────────────────────┐
│                     External Data Sources                 │
│  USDA AMS API │ Hoyt Report │ NOAA │ NASS │ EIA │ Others │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│                   Data Ingestion Layer                    │
│    Scheduler (Airflow/Prefect) → ETL Workers →           │
│    Validation → Raw Storage (S3/GCS)                     │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│                Feature Engineering Layer                  │
│    Price normalization │ Lag features │ Rolling averages  │
│    Drought index join  │ Seasonal encoding                │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────┐   ┌──────────────────────┐
│     ML Model Layer          │   │    Model Registry     │
│  Time-series models:        │◄──│  MLflow / W&B        │
│  • XGBoost (baseline)       │   │  Versioning          │
│  • Prophet (seasonality)    │   │  A/B evaluation      │
│  • LSTM (deep learning)     │   └──────────────────────┘
└──────────────┬──────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│                 Backend API (FastAPI / Python)            │
│   /forecasts  /prices  /reports  /alerts  /webhooks      │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│                  Frontend (React / Next.js)               │
│   Dashboard │ Forecast Charts │ Alerts │ Explorer        │
└──────────────────────────────────────────────────────────┘
```

### 7.2 Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Backend API** | Python, FastAPI | Fast async API, Python ML ecosystem |
| **Frontend** | React + Next.js | SSR for SEO, chart libraries |
| **Database** | PostgreSQL (TimescaleDB extension) | Native time-series optimization |
| **Data Lake** | AWS S3 or GCS | Raw report storage, versioned |
| **Orchestration** | Apache Airflow or Prefect | DAG-based ETL scheduling |
| **ML Training** | scikit-learn, XGBoost, Facebook Prophet, PyTorch (LSTM) | Coverage of baseline to deep learning |
| **Model Registry** | MLflow | Experiment tracking, model versioning |
| **Charting** | Recharts or Plotly.js | Interactive time-series visualization |
| **Cache** | Redis | API response caching, session store |
| **Auth** | Auth0 or Supabase Auth | OAuth2, user management |
| **Notifications** | SendGrid (email) + FCM (push) | Reliable alert delivery |
| **Infrastructure** | Docker, Kubernetes (or Railway/Render for MVP) | Scalable deployment |
| **CI/CD** | GitHub Actions | Automated testing and deployment |

---

## 8. API Integrations

### 8.1 USDA AMS Market News API

```
Base URL:    https://marsapi.ams.usda.gov/services/v1.2
Auth:        API key in header: "Authorization: Bearer <key>"
Rate limit:  1000 requests/day (free tier)

Key Endpoints:
  GET /reports
      → List available report slugs

  GET /reports/{slug_id}
      → Fetch latest report data (JSON)
      → Query params: ?q=commodity:Alfalfa&allSections=true

  GET /reports/{slug_id}/{report_date}
      → Fetch report for a specific date

California Direct Hay Report slug: LM_GR212
Response fields: report_date, commodity, grade, region,
                 price_low, price_high, price_wtavg, volume, unit
```

### 8.2 USDA NASS API

```
Base URL:    https://quickstats.nass.usda.gov/api
Auth:        API key (query param: key=<key>)

Key call:
  GET /api/GET?key=<key>&source_desc=SURVEY
      &sector_desc=CROPS&commodity_desc=HAY
      &statisticcat_desc=PRODUCTION
      &state_name=CALIFORNIA&format=JSON
```

### 8.3 NOAA Climate Data Online API

```
Base URL:    https://www.ncdc.noaa.gov/cdo-web/api/v2
Auth:        Token in header: "token: <key>"

Key call:
  GET /data?datasetid=GHCND&stationid=<CA_station>
      &startdate=<date>&enddate=<date>
      &datatypeid=PRCP,TMAX,TMIN&limit=1000
```

### 8.4 EIA Open Data API (Diesel Prices)

```
Base URL:    https://api.eia.gov/v2
Auth:        API key (query param: api_key=<key>)

Key call:
  GET /petroleum/pri/gnd/data/
      ?api_key=<key>&frequency=weekly
      &data[0]=value&facets[product][]=EPD2DXL0
      &facets[area][]=CA
```

### 8.5 U.S. Drought Monitor API

```
Base URL:    https://droughtmonitor.unl.edu/api
Auth:        None required (public)

Key call:
  GET /api/webservice/comprehensivestats/
      ?aoi=county&aoitext=California
      &date=<YYYY-MM-DD>&statisticsType=1
```

---

## 9. Machine Learning Model

### 9.1 Prediction Targets

| Target | Description |
|--------|-------------|
| `price_wtavg_1w` | Weighted average price, 1-week ahead |
| `price_wtavg_2w` | Weighted average price, 2-weeks ahead |
| `price_wtavg_4w` | Weighted average price, 4-weeks ahead |
| `price_wtavg_12w` | Weighted average price, 12-weeks ahead |

Per segment: `{region} × {hay_type} × {grade}` (e.g., Central CA × Alfalfa × Premium)

### 9.2 Feature Set

**Price Lag Features**
- Price at t-1, t-2, t-4, t-8 weeks
- 4-week and 12-week rolling average
- 52-week YoY change

**Supply Signals**
- CA hay production (NASS)
- National hay stocks (NASS)
- Alfalfa crop cutting progress (NASS)

**Demand Signals**
- Dairy herd size (NASS)
- Cattle on feed (NASS)
- Hay export volume (USDA FAS)

**Environmental Signals**
- PDSI drought index (NOAA)
- Drought Monitor D3/D4 coverage (%)
- 30-day precipitation anomaly (NOAA)
- Cooling Degree Days (heat stress for alfalfa)
- CA irrigation water availability

**Cost Signals**
- Weekly diesel price (EIA)
- CPI animal feeds (BLS)

**Market Context**
- Seasonal month/week encoding (sine-cosine)
- CME corn and soy price (feed substitute correlation)

**Sentiment**
- Hoyt Report NLP bullish/bearish score

### 9.3 Model Selection Strategy

| Model | Role | Notes |
|-------|------|-------|
| **XGBoost** | Primary baseline | Handles mixed features well, interpretable |
| **Facebook Prophet** | Seasonality decomposition | Captures annual/quarterly hay cutting cycles |
| **LSTM (PyTorch)** | Long-range dependencies | Captures multi-year drought cycles |
| **Ensemble** | Production model | Weighted average of above; weights tuned on validation set |

### 9.4 Evaluation Protocol

- **Train / Validation / Test split:** 70% / 15% / 15% (time-ordered, no leakage)
- **Walk-forward validation:** Simulate weekly retraining over the test period
- **Metrics:** MAPE, RMSE, directional accuracy (up/down)
- **Baseline:** Naïve persistence model (last observed price = next week's price)

### 9.5 Retraining Schedule

- Weekly automated retraining after new USDA report ingestion
- Model promoted to production only if MAPE improves over holdout set vs. current production model

---

## 10. User Interface

### 10.1 Key Screens

#### 10.1.1 Main Dashboard
```
┌────────────────────────────────────────────────────────┐
│ HAY PRICE PREDICTOR          [Region▼] [Type▼] [Grade▼]│
├─────────────────────────────┬──────────────────────────┤
│                             │  CURRENT PRICE           │
│   Price Trend Chart         │  Premium Alfalfa, Central│
│   (historical + forecast)   │  $285 / ton              │
│   ─────────────── ╌╌╌╌╌╌╌ │  ▲ +$12 vs. 4 weeks ago  │
│                             ├──────────────────────────┤
│                             │  4-WEEK FORECAST         │
│                             │  $278 – $294 / ton       │
│                             │  (90% confidence)        │
├─────────────────────────────┴──────────────────────────┤
│ KEY DRIVERS:  Drought D2 coverage +5% ▲  |  Diesel ▼  │
│              Export demand stable       |  Stocks ▼   │
└────────────────────────────────────────────────────────┘
```

#### 10.1.2 Forecast Detail View
- Extended chart (12-week forecast)
- Confidence band selector (80% / 95%)
- Scenario panel: adjust drought severity or diesel price, see forecast shift
- Feature importance bar chart

#### 10.1.3 Historical Explorer
- Date-range picker
- Multi-series comparison (e.g., Northern CA vs. Southern CA Alfalfa)
- Export button (CSV / Excel)
- Event annotation layer (USDA drought declarations, export bans, etc.)

#### 10.1.4 Alerts Manager
- Create alert: region + hay type + grade + threshold + direction (above/below)
- Active alerts list with toggle
- Alert history with triggered timestamps

### 10.2 Design Principles

- Mobile-first responsive layout
- Accessible (WCAG 2.1 AA)
- No jargon — hay types and grades explained via tooltips
- Fast: < 2s page load for dashboard (cached API responses)

---

## 11. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance** | Dashboard initial load < 2s; forecast API response < 500ms (cached) |
| **Availability** | 99.5% uptime SLA (excluding scheduled maintenance) |
| **Data freshness** | Price data refreshed within 24h of USDA report publication |
| **Scalability** | Support 10,000 daily active users at launch; horizontally scalable |
| **Security** | HTTPS everywhere; API keys hashed at rest; OWASP Top 10 mitigated |
| **Privacy** | No PII collected beyond email for alert notifications; CCPA compliant |
| **Data retention** | Raw ingested data retained for 10 years; predictions retained for 5 years |
| **Observability** | Structured logging; Prometheus metrics; Sentry error tracking |

---

## 12. Success Metrics

### 12.1 Model Performance

| Metric | Target |
|--------|--------|
| 1-week MAPE | ≤ 5% |
| 4-week MAPE | ≤ 8% |
| 12-week MAPE | ≤ 14% |
| Directional accuracy (up/down) | ≥ 70% |

### 12.2 Product Metrics (6 months post-launch)

| Metric | Target |
|--------|--------|
| Monthly Active Users | 2,000 |
| Data source uptime | ≥ 98% ingestion success rate |
| Alert delivery latency | < 5 minutes from trigger |
| User retention (D30) | ≥ 40% |
| Paid API tier conversion | ≥ 3% of registered users |

---

## 13. Phased Rollout

### Phase 1 — Data Foundation (Weeks 1–6)
- [ ] USDA AMS API integration and ingestion pipeline
- [ ] Hoyt Report ETL pipeline (PDF/email parser)
- [ ] Supplemental source integrations (NOAA, NASS, EIA, Drought Monitor)
- [ ] TimescaleDB schema design and migrations
- [ ] Raw data storage in S3/GCS with versioning
- [ ] Ingestion audit logs and failure alerting
- [ ] Basic price dashboard (historical data only, no forecast)

### Phase 2 — Forecast Engine + Core Product (Weeks 7–14)
- [ ] Feature engineering pipeline
- [ ] Baseline XGBoost model training and evaluation
- [ ] Prophet and LSTM model training
- [ ] Ensemble model and model registry (MLflow)
- [ ] Forecast API endpoint
- [ ] Forecast chart with confidence intervals on dashboard
- [ ] Feature importance panel
- [ ] Alert system (threshold-based, email notifications)
- [ ] Historical data export (CSV)
- [ ] User authentication and profile management

### Phase 3 — Advanced Features + Growth (Weeks 15–22)
- [ ] Scenario analysis ("what-if" drought adjustment)
- [ ] Market commentary NLP feed (Hoyt Report sentiment)
- [ ] Developer REST API with key management
- [ ] Additional regions (Pacific Northwest, Desert Southwest)
- [ ] Mobile app (React Native or PWA)
- [ ] Enterprise / API tier pricing model
- [ ] Marketing site and SEO content

---

## 14. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Hoyt Report format changes break ETL | Medium | High | Version-detect parser; email alert on parse failure; manual fallback |
| USDA AMS API changes endpoint structure | Low | High | Pin API version; monitor USDA AMS changelog; integration tests on every ingestion run |
| Insufficient historical data for model training | Medium | High | Supplement with NASS national data; use transfer learning across regions |
| Drought/weather causes extreme price spike outside model training distribution | Medium | High | Add prediction uncertainty flag; display "market stress" warning when features are out of distribution |
| Data licensing restrictions on Hoyt Report | Medium | Medium | Review Hoyt Terms of Service; contact publisher for data partnership agreement |
| Low user adoption without marketing | High | Medium | Launch with free tier; partner with UC Cooperative Extension and Farm Bureau for distribution |
| MAPE target not met at launch | Medium | Medium | Set conservative public forecast horizons (4-week max) until model matures; show baseline comparisons |

---

## 15. Open Questions

1. **Hoyt Report Access:** Does the Hoyt Report publisher offer a structured data feed or API, or is PDF/email parsing the only path? Is there a licensing agreement required?

2. **Forecast Granularity:** Should forecasts be at the county level, or is regional (Northern/Central/Southern/Desert CA) sufficient for v1?

3. **Additional Regions:** Which regions beyond California should be prioritized for Phase 3 — Pacific Northwest, Arizona, or others?

4. **Monetization Model:** Is the business model freemium (free dashboard, paid API/alerts), subscription-based, or enterprise licensing?

5. **Export Market Data:** USDA FAS export data for compressed hay (primarily alfalfa to Japan, South Korea, China) is a significant demand driver. Should this be a Phase 1 or Phase 2 integration?

6. **Water Data Freshness:** California water availability data can be delayed. Is real-time water futures (e.g., NQH2O) a better proxy for alfalfa production risk?

7. **Mobile Priority:** Is a responsive web app sufficient for launch, or is a native mobile app required from the start?

---

## Appendix A: Hay Grade Reference

| Grade | Description | Typical Use |
|-------|-------------|-------------|
| Supreme | RFV > 185, very high digestibility | Dairy, performance horses |
| Premium | RFV 170–185 | Dairy, horses |
| Good | RFV 150–170 | Beef cattle, horses |
| Fair | RFV 130–150 | Beef cattle, sheep |
| Utility | RFV < 130 | Backgrounding, low-value livestock |

RFV = Relative Feed Value (USDA grading standard)

---

## Appendix B: California Hay Market Regions

| Region | Key Counties | Primary Hay Type |
|--------|-------------|-----------------|
| Northern California | Shasta, Lassen, Modoc, Siskiyou | Alfalfa, Grass |
| Sacramento Valley | Sacramento, Yolo, Glenn, Colusa | Alfalfa, Mixed |
| San Joaquin Valley | Fresno, Tulare, Kern, Kings | Alfalfa, Sudan |
| Southern California / Desert | Imperial, Riverside, San Bernardino | Alfalfa (desert cut) |
| Coastal | Marin, Sonoma, Santa Barbara | Grass, Oat |

---

*This document is a living specification. Sections will be updated as requirements are clarified and development progresses.*
