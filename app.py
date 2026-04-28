import os, requests, time

# ── Google Drive file loader ──────────────────────────────────────────────
def _gdrive_download(file_id, dest_path):
    if os.path.exists(dest_path):
        return
    parent = os.path.dirname(dest_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    session = requests.Session()
    response = session.get(url, stream=True)
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm={value}"
            response = session.get(url, stream=True)
            break
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)

DRIVE_FILES = {
    "models/xgboost_v12f_20260427_235122.pkl": "1C0F0DMaGqJcghOfSpsOZQiOjsMUExmOO",
    "model_registry.csv":                       "19udmUo0SUKMN1Pr2kn0JUDReK-5HgEeG",
    "ca_hay_prices_v2_clean.csv":               "1kpOqZAEDn_Ha_xKkePdwlhuuqyVUfH23",
    "weather_weekly.csv":                       "1l8w3ZOjPcV8LkZd2rhraNcHVBK0TX0uv",
    "diesel_prices.csv":                        "1w5KT_ztHZg8V8TzUP3T9q8HmfKHGAO8D",
    "cattle_monthly_cap.csv":                   "189jbu4pVGqrPNokGgBJO55as_3sHrxXm",
    "milk_price_ca_clean.csv":                  "1GtzUt5_O4XUuYMlVt2_-xIYKiuKqJgmq",
    "water_allocation.csv":                     "1-CivDzDJ3dlFeKDa5zu5JxuoA2N77WmH",
    "hay_stocks_features.csv":                  "1aiVJpM1xYVmqTURCipoFUFcrw76Ae42d",
    "nass_supply_data.csv":                     "1MW6FqQcSPkaUEnQ61NFj9s8aVDjYdZ_L",
    "zip_to_region.json":                       "1LAVGV7KoDrJXgv9WkJoxSqT4ThKopGuU",
}

for local_path, file_id in DRIVE_FILES.items():
    _gdrive_download(file_id, local_path)

# ── Imports ───────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HayDay.ai",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Nunito+Sans:wght@400;600&display=swap');

*, html, body, [class*="css"] {
    font-family: "Nunito Sans", sans-serif;
    box-sizing: border-box;
}
.stApp {
    background: #F5F0E8;
    color: #1C1C1E;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 48px 20px 80px !important;
    max-width: 640px !important;
    margin: 0 auto;
}

/* Logo */
.hayday-logo {
    text-align: center;
    margin-bottom: 8px;
}
.hayday-logo-text {
    font-family: "Nunito", sans-serif;
    font-size: 42px;
    font-weight: 800;
    color: #1C1C1E;
    letter-spacing: -1px;
}
.hayday-logo-ai {
    color: #C17F3E;
}
.hayday-tagline {
    text-align: center;
    font-size: 15px;
    color: #8B7355;
    margin-bottom: 36px;
    font-family: "Nunito Sans", sans-serif;
}

/* Input card */
.input-card {
    background: #FFFFFF;
    border-radius: 20px;
    padding: 28px 24px;
    box-shadow: 0 2px 20px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}

/* Region pill */
.region-pill {
    background: #F0FAF4;
    border: 1.5px solid #B8E6C8;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 13px;
    color: #1A7A40;
    margin-top: -4px;
    margin-bottom: 8px;
}
.region-pill-warn {
    background: #FFFBF0;
    border: 1.5px solid #FFE9A0;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 13px;
    color: #B07D00;
    margin-top: -4px;
    margin-bottom: 8px;
}

/* Button */
.stButton > button {
    width: 100%;
    background: #C17F3E !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 14px !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    font-family: "Nunito", sans-serif !important;
    cursor: pointer !important;
    margin-top: 8px;
    transition: background 0.2s;
}
.stButton > button:hover {
    background: #A86D32 !important;
}

/* Loading */
.loading-wrap {
    text-align: center;
    padding: 80px 0 60px;
}
.loading-bale {
    font-size: 80px;
    display: inline-block;
    animation: rotateBale 1.2s linear infinite;
}
@keyframes rotateBale {
    0%   { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
.loading-text {
    color: #8B7355;
    font-size: 15px;
    margin-top: 20px;
    font-family: "Nunito Sans", sans-serif;
}

/* Result card */
.result-card {
    background: #FFFFFF;
    border-radius: 20px;
    padding: 32px 28px;
    box-shadow: 0 2px 24px rgba(0,0,0,0.07);
    margin-top: 20px;
}
.result-meta {
    font-size: 13px;
    color: #8B7355;
    margin-bottom: 6px;
}
.result-price {
    font-family: "Nunito", sans-serif;
    font-size: 60px;
    font-weight: 800;
    color: #1C1C1E;
    line-height: 1.0;
    letter-spacing: -2px;
}
.result-unit {
    font-size: 20px;
    color: #8B7355;
    font-weight: 400;
    letter-spacing: 0;
}
.result-range {
    font-size: 14px;
    color: #8B7355;
    margin-top: 6px;
}
.result-trend-up {
    font-size: 15px;
    color: #1A7A40;
    font-weight: 700;
    margin-top: 14px;
}
.result-trend-down {
    font-size: 15px;
    color: #C0392B;
    font-weight: 700;
    margin-top: 14px;
}
.divider {
    border: none;
    border-top: 1px solid #F0EAE0;
    margin: 20px 0;
}
.stat-row {
    display: flex;
    gap: 10px;
    justify-content: space-between;
}
.stat-chip {
    background: #F5F0E8;
    border-radius: 12px;
    padding: 12px 10px;
    flex: 1;
    text-align: center;
}
.stat-icon { font-size: 18px; }
.stat-label {
    font-size: 10px;
    color: #8B7355;
    margin-top: 2px;
}
.stat-value {
    font-size: 13px;
    font-weight: 700;
    color: #1C1C1E;
    margin-top: 2px;
}
.result-disclaimer {
    font-size: 11px;
    color: #B0A090;
    text-align: center;
    margin-top: 16px;
}
.powered-by {
    text-align: center;
    font-size: 11px;
    color: #B0A090;
    margin-top: 20px;
}

/* Streamlit widget label */
.stTextInput label, .stSelectbox label {
    font-family: "Nunito Sans", sans-serif !important;
    font-size: 13px !important;
    color: #8B7355 !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Load zip map ──────────────────────────────────────────────────────────
_zip_map = {}
if os.path.exists("zip_to_region.json"):
    with open("zip_to_region.json") as _zf:
        _zip_map = json.load(_zf)

# ── Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hayday-logo">
  <span class="hayday-logo-text">HayDay<span class="hayday-logo-ai">.ai</span></span>
</div>
<p class="hayday-tagline">California hay prices, predicted.</p>
""", unsafe_allow_html=True)

# ── Input card ────────────────────────────────────────────────────────────
st.markdown('<div class="input-card">', unsafe_allow_html=True)

zip_input = st.text_input("ZIP Code", placeholder="e.g. 93274", max_chars=5)

# ZIP → region
zip_clean   = zip_input.strip() if zip_input else ""
auto_region = _zip_map.get(zip_clean, None)

if zip_clean and len(zip_clean) == 5 and zip_clean.isdigit():
    if auto_region:
        st.markdown(f'<div class="region-pill">📍 {auto_region}</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="region-pill-warn">📍 ZIP not in service area — select region below</div>',
                    unsafe_allow_html=True)

# Region fallback selector
REGION_OPTIONS = [
    "Southeast",
    "North San Joaquin Valley",
    "Sacramento Valley",
    "North Inter-Mountains",
    "Central San Joaquin Valley",
]
if auto_region and auto_region in REGION_OPTIONS:
    region_index = REGION_OPTIONS.index(auto_region)
    region = REGION_OPTIONS[region_index]
else:
    region = st.selectbox("Region", REGION_OPTIONS)

grade    = st.selectbox("Hay Grade", ["Supreme", "Premium", "Good", "Fair"])
delivery = st.selectbox("Delivery", ["Delivered", "FOB Stack"])

get_price = st.button("Get Price →")
st.markdown('</div>', unsafe_allow_html=True)

# ── Prediction ────────────────────────────────────────────────────────────
if get_price:

    # Loading animation
    loading = st.empty()
    loading.markdown("""
    <div class="loading-wrap">
      <div class="loading-bale">🌾</div>
      <p class="loading-text">Analyzing California hay market…</p>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(5)
    loading.empty()

    try:
        # Load model
        bundle   = joblib.load("models/xgboost_v12f_20260427_235122.pkl")
        model    = bundle["model"]
        features = bundle["features"]
        encoders = bundle["encoders"]

        # Load data
        diesel = pd.read_csv("diesel_prices.csv", parse_dates=["date"])
        milk   = pd.read_csv("milk_price_ca_clean.csv")
        cattle = pd.read_csv("cattle_monthly_cap.csv")
        stocks = pd.read_csv("hay_stocks_features.csv")
        water  = pd.read_csv("water_allocation.csv")
        nass   = pd.read_csv("nass_supply_data.csv")
        prices = pd.read_csv("ca_hay_prices_v2_clean.csv", parse_dates=["date"])

        now   = datetime.now()
        year  = now.year
        month = now.month
        week  = int(now.isocalendar()[1])

        # Seasonality
        month_sin = np.sin(2 * np.pi * month / 12)
        month_cos = np.cos(2 * np.pi * month / 12)
        week_sin  = np.sin(2 * np.pi * week / 52)
        week_cos  = np.cos(2 * np.pi * week / 52)
        quarter   = (month - 1) // 3 + 1

        # Encode categoricals safely
        def safe_encode(encoder, value, fallback=0):
            try:
                return encoder.transform([value])[0]
            except Exception:
                return fallback

        region_enc    = safe_encode(encoders["region"],    region)
        quality_enc   = safe_encode(encoders["quality"],   grade)
        commodity_enc = safe_encode(encoders["commodity"], "Hay")

        # Price lags
        recent = prices[
            (prices["region"] == region) &
            (prices["quality"].str.contains(grade, case=False, na=False))
        ].sort_values("date").tail(20)

        price_fallback = prices[prices["region"] == region]["price_avg"].median()
        lag_4w       = float(recent["price_avg"].iloc[-4])  if len(recent) >= 4  else price_fallback
        lag_13w      = float(recent["price_avg"].iloc[-13]) if len(recent) >= 13 else price_fallback
        roll_4w_mean = float(recent["price_avg"].tail(4).mean()) if len(recent) >= 1 else price_fallback
        last_price   = float(recent["price_avg"].iloc[-1]) if len(recent) >= 1 else price_fallback

        # Diesel
        diesel_s     = diesel.sort_values("date")
        diesel_4w_avg  = float(diesel_s.tail(4)["diesel_price"].mean())
        diesel_13w_avg = float(diesel_s.tail(13)["diesel_price"].mean())

        # Milk
        milk["month"] = milk["month"].astype(int)
        milk_row = milk[(milk["year"] == year) & (milk["month"] == month)]
        if milk_row.empty:
            milk_row = milk.sort_values(["year", "month"]).tail(1)
        milk_price_cwt = float(milk_row["milk_price_cwt"].values[0])

        # Cattle
        cattle["month"] = cattle["month"].astype(int)
        cat_row = cattle[(cattle["year"] == year) & (cattle["month"] == month)]
        if cat_row.empty:
            cat_row = cattle.sort_values(["year", "month"]).tail(1)
        cattle_on_feed_ca = float(cat_row["cattle_on_feed_ca"].values[0])

        # Annual
        def latest_row(df, yr):
            r = df[df["year"] == yr]
            return r if not r.empty else df.sort_values("year").tail(1)

        stocks_row = latest_row(stocks, year)
        water_row  = latest_row(water,  year)
        nass_row   = latest_row(nass,   year)

        stocks_may         = float(stocks_row["stocks_may"].values[0])
        stocks_may_yoy     = float(stocks_row["stocks_may_yoy"].values[0])
        avg_allocation     = float(water_row["avg_allocation"].values[0])
        drought_year       = float(water_row["drought_year"].values[0])
        production_tons    = float(nass_row["production_tons"].values[0])
        acres_harvested    = float(nass_row["acres_harvested"].values[0])
        yield_tons_per_acre= float(nass_row["yield_tons_per_acre"].values[0])
        alfalfa_share      = float(nass_row["alfalfa_share"].values[0])

        # Hay attributes
        is_alfalfa      = 1 if grade in ["Supreme", "Premium"] else 0
        is_delivered    = 1 if delivery == "Delivered" else 0
        is_dairy_buyer  = 1
        is_large_square = 1
        has_quality_issue = 0

        row = {
            "month_sin": month_sin, "month_cos": month_cos,
            "week_sin": week_sin,   "week_cos": week_cos,
            "quarter": quarter,
            "region_enc": region_enc, "quality_enc": quality_enc,
            "commodity_enc": commodity_enc,
            "lag_4w": lag_4w, "lag_13w": lag_13w, "roll_4w_mean": roll_4w_mean,
            "diesel_4w_avg": diesel_4w_avg, "diesel_13w_avg": diesel_13w_avg,
            "milk_price_cwt": milk_price_cwt,
            "cattle_on_feed_ca": cattle_on_feed_ca,
            "stocks_may": stocks_may, "stocks_may_yoy": stocks_may_yoy,
            "avg_allocation": avg_allocation, "drought_year": drought_year,
            "production_tons": production_tons, "acres_harvested": acres_harvested,
            "yield_tons_per_acre": yield_tons_per_acre, "alfalfa_share": alfalfa_share,
            "is_alfalfa": is_alfalfa, "is_delivered": is_delivered,
            "is_dairy_buyer": is_dairy_buyer, "is_large_square": is_large_square,
            "has_quality_issue": has_quality_issue,
        }

        X = pd.DataFrame([row])[features].astype(float)
        pred_price = float(model.predict(X)[0])
        ci_low     = max(0, round(pred_price - 24.76, 0))
        ci_high    = round(pred_price + 24.76, 0)
        pred_price = round(pred_price, 0)

        # Trend
        trend_pct   = ((pred_price - last_price) / last_price * 100) if last_price else 0
        trend_arrow = "↑" if trend_pct >= 0 else "↓"
        trend_cls   = "result-trend-up" if trend_pct >= 0 else "result-trend-down"

        # Result card
        st.markdown(f"""
        <div class="result-card">
          <div class="result-meta">{region} · {grade} · {delivery}</div>
          <div class="result-price">${pred_price:,.0f}<span class="result-unit"> /ton</span></div>
          <div class="result-range">Range: ${ci_low:,.0f} – ${ci_high:,.0f}/ton</div>
          <div class="{trend_cls}">{trend_arrow} {abs(trend_pct):.1f}% vs last reported</div>
          <hr class="divider">
          <div class="stat-row">
            <div class="stat-chip">
              <div class="stat-icon">🐄</div>
              <div class="stat-label">Cattle on feed</div>
              <div class="stat-value">{cattle_on_feed_ca/1000:.0f}K head</div>
            </div>
            <div class="stat-chip">
              <div class="stat-icon">⛽</div>
              <div class="stat-label">Diesel 4w avg</div>
              <div class="stat-value">${diesel_4w_avg:.2f}/gal</div>
            </div>
            <div class="stat-chip">
              <div class="stat-icon">🥛</div>
              <div class="stat-label">Milk price</div>
              <div class="stat-value">${milk_price_cwt:.2f}/cwt</div>
            </div>
          </div>
          <div class="result-disclaimer">
            ±$24.76/ton model accuracy · Week of {now.strftime('%B %d, %Y')}
          </div>
        </div>
        <div class="powered-by">
          Powered by USDA AMS · NASS · Open-Meteo · EIA Diesel
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Something went wrong: {e}")
        st.info("Try refreshing — the model may still be loading.")
