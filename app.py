"""HayDay.ai — California hay price prediction dashboard."""
from __future__ import annotations

import json
import math
import os
import time
from datetime import date

import joblib
import numpy as np
import pandas as pd
import requests
import streamlit as st

# ── Google Drive file registry ────────────────────────────────────────────────

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


def _gdrive_download(file_id: str, dest_path: str) -> None:
    """Download a Google Drive file to dest_path if not already present."""
    os.makedirs(os.path.dirname(dest_path) if os.path.dirname(dest_path) else ".", exist_ok=True)
    if os.path.exists(dest_path):
        return
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    session = requests.Session()
    resp = session.get(url, stream=True)
    token = next(
        (v for k, v in resp.cookies.items() if k.startswith("download_warning")),
        None,
    )
    if token:
        resp = session.get(url, params={"confirm": token}, stream=True)
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(32768):
            if chunk:
                f.write(chunk)


def _ensure_files() -> None:
    for local_path, file_id in DRIVE_FILES.items():
        try:
            _gdrive_download(file_id, local_path)
        except Exception:
            pass


# ── Constants ─────────────────────────────────────────────────────────────────

MODEL_MAE = 24.76

GRADE_OPTIONS = ["Supreme", "Premium", "Good", "Fair"]
DELIVERY_OPTIONS = ["Delivered", "FOB Stack"]

REGION_DISPLAY: dict[str, str] = {
    "northern_ca": "Northern California",
    "northern":    "Northern California",
    "central_valley": "Central San Joaquin Valley",
    "central":     "Central San Joaquin Valley",
    "central_ca":  "Central San Joaquin Valley",
    "san_joaquin": "Central San Joaquin Valley",
    "southern_ca": "Southern California",
    "southern":    "Southern California",
    "central_coast": "Central Coast",
    "coast":       "Central Coast",
    "imperial":    "Imperial Valley",
    "desert":      "Desert / Imperial Valley",
}

# ── Global CSS ────────────────────────────────────────────────────────────────

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Nunito+Sans:ital,wght@0,400;0,600;1,400&display=swap');

/* Page shell */
html, body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background-color: #F5F0E8 !important;
    font-family: 'Nunito Sans', sans-serif;
    color: #1C1C1E;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header,
.stDeployButton,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
}
section[data-testid="stSidebar"] { display: none !important; }

/* Centered narrow layout */
.block-container {
    max-width: 680px !important;
    padding: 0 1.25rem 5rem !important;
    margin: 0 auto !important;
}

/* ── Input labels ── */
.stTextInput label,
.stSelectbox label {
    font-family: 'Nunito', sans-serif !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: #8B7355 !important;
    margin-bottom: 2px !important;
}

/* ── Text input ── */
.stTextInput > div > div > input {
    border: 1.5px solid #E0D8CC !important;
    border-radius: 12px !important;
    background: #FFFFFF !important;
    font-family: 'Nunito Sans', sans-serif !important;
    font-size: 16px !important;
    color: #1C1C1E !important;
    padding: 11px 16px !important;
    height: auto !important;
    box-shadow: none !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextInput > div > div > input:focus {
    border-color: #C17F3E !important;
    box-shadow: 0 0 0 3px rgba(193,127,62,0.14) !important;
    outline: none !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    border: 1.5px solid #E0D8CC !important;
    border-radius: 12px !important;
    background: #FFFFFF !important;
    font-family: 'Nunito Sans', sans-serif !important;
    font-size: 16px !important;
    color: #1C1C1E !important;
    min-height: 46px !important;
}
.stSelectbox > div > div:focus-within {
    border-color: #C17F3E !important;
    box-shadow: 0 0 0 3px rgba(193,127,62,0.14) !important;
}

/* ── Primary / all buttons ── */
.stButton > button {
    background: #C17F3E !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 14px !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 800 !important;
    font-size: 17px !important;
    padding: 14px 0 !important;
    width: 100% !important;
    cursor: pointer !important;
    letter-spacing: 0.02em !important;
    transition: background 0.15s, box-shadow 0.15s, transform 0.1s !important;
}
.stButton > button:hover {
    background: #A86D30 !important;
    box-shadow: 0 4px 18px rgba(193,127,62,0.38) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* Secondary "back" button override */
button[data-testid="back-btn"] {
    background: transparent !important;
    color: #8B7355 !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    border: 1.5px solid #E0D8CC !important;
}
button[data-testid="back-btn"]:hover {
    background: #FFFFFF !important;
    box-shadow: none !important;
    transform: none !important;
}

/* Card border wrapper (st.container with border=True) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border: none !important;
    border-radius: 20px !important;
    box-shadow: 0 4px 28px rgba(0,0,0,0.08) !important;
    padding: 28px 32px 24px !important;
}

/* Animations */
@keyframes spin {
    0%   { transform: rotate(0deg) scale(1); }
    50%  { transform: rotate(180deg) scale(1.2); }
    100% { transform: rotate(360deg) scale(1); }
}
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0); }
}
</style>
"""

# ── Cached loaders ────────────────────────────────────────────────────────────

@st.cache_resource
def load_model_bundle() -> dict | None:
    try:
        if not os.path.exists("model_registry.csv"):
            return None
        registry = pd.read_csv("model_registry.csv")
        prod_mask = registry["is_production"].astype(str).str.lower().isin(["true", "1", "yes"])
        prod_rows = registry[prod_mask]
        if prod_rows.empty:
            return None
        model_path = None
        for col in ("model_path", "path", "file_path", "filename"):
            if col in prod_rows.columns:
                model_path = str(prod_rows.iloc[0][col]).strip()
                break
        if not model_path or not os.path.exists(model_path):
            for fname in DRIVE_FILES:
                if fname.endswith(".pkl") and os.path.exists(fname):
                    model_path = fname
                    break
            else:
                return None
        bundle = joblib.load(model_path)
        if not isinstance(bundle, dict):
            bundle = {"model": bundle, "features": [], "encoders": {}}
        return bundle
    except Exception:
        return None


@st.cache_data
def load_support_data() -> dict[str, pd.DataFrame | None]:
    result: dict[str, pd.DataFrame | None] = {}
    for key, fname in [
        ("hay",     "ca_hay_prices_v2_clean.csv"),
        ("diesel",  "diesel_prices.csv"),
        ("milk",    "milk_price_ca_clean.csv"),
        ("cattle",  "cattle_monthly_cap.csv"),
        ("stocks",  "hay_stocks_features.csv"),
        ("water",   "water_allocation.csv"),
        ("nass",    "nass_supply_data.csv"),
    ]:
        try:
            result[key] = pd.read_csv(fname) if os.path.exists(fname) else None
        except Exception:
            result[key] = None
    return result


@st.cache_data
def load_zip_map() -> dict:
    try:
        if os.path.exists("zip_to_region.json"):
            with open("zip_to_region.json") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


# ── Feature helpers ───────────────────────────────────────────────────────────

def _safe_last(df: pd.DataFrame | None, keywords: list[str], default: float) -> float:
    if df is None or df.empty:
        return default
    for kw in keywords:
        cols = [c for c in df.columns if kw.lower() in c.lower()]
        if cols:
            try:
                return float(df[cols[0]].dropna().iloc[-1])
            except Exception:
                pass
    return default


def _rolling_mean(df: pd.DataFrame | None, keywords: list[str], n: int, default: float) -> float:
    if df is None or df.empty:
        return default
    for kw in keywords:
        cols = [c for c in df.columns if kw.lower() in c.lower()]
        if cols:
            try:
                return float(df[cols[0]].dropna().tail(n).mean())
            except Exception:
                pass
    return default


def _encode(encoders: dict, key: str, value: str, default: int = 0) -> int:
    enc = encoders.get(key)
    if enc is None:
        return default
    try:
        classes = list(enc.classes_)
        if value in classes:
            return int(enc.transform([value])[0])
        lower_map = {c.lower(): c for c in classes}
        if value.lower() in lower_map:
            return int(enc.transform([lower_map[value.lower()]])[0])
    except Exception:
        pass
    return default


def build_feature_row(
    region: str,
    quality: str,
    is_delivered: int,
    target_date: date,
    dfs: dict,
    bundle: dict,
) -> pd.DataFrame:
    month    = target_date.month
    week_num = int(target_date.isocalendar().week)
    quarter  = (month - 1) // 3 + 1

    encoders     = bundle.get("encoders") or {}
    feature_names: list[str] = bundle.get("features") or []

    # Price lags from historical data
    lag_4w = roll_4w_mean = lag_13w = 215.0
    hay_df = dfs.get("hay")
    if hay_df is not None and not hay_df.empty:
        date_col    = next((c for c in hay_df.columns if "date" in c.lower()), None)
        price_col   = next((c for c in hay_df.columns if "price" in c.lower() or "wtavg" in c.lower()), None)
        region_col  = next((c for c in hay_df.columns if "region" in c.lower()), None)
        quality_col = next((c for c in hay_df.columns if "quality" in c.lower() or "grade" in c.lower()), None)

        seg = hay_df.copy()
        if region_col:
            seg = seg[seg[region_col].astype(str).str.lower() == region.lower()]
        if quality_col:
            seg = seg[seg[quality_col].astype(str).str.lower() == quality.lower()]
        if date_col:
            seg = seg.sort_values(date_col)
        if price_col and not seg.empty:
            prices = seg[price_col].dropna().values.astype(float)
            if len(prices) >= 4:
                lag_4w        = float(prices[-4])
                roll_4w_mean  = float(np.mean(prices[-4:]))
                lag_13w       = float(prices[-13]) if len(prices) >= 13 else float(prices[0])

    features: dict[str, float] = {
        "month_sin":         math.sin(2 * math.pi * month / 12),
        "month_cos":         math.cos(2 * math.pi * month / 12),
        "week_sin":          math.sin(2 * math.pi * week_num / 52),
        "week_cos":          math.cos(2 * math.pi * week_num / 52),
        "quarter":           float(quarter),
        "region_enc":        float(_encode(encoders, "region", region)),
        "quality_enc":       float(_encode(encoders, "quality", quality)),
        "commodity_enc":     float(_encode(encoders, "commodity", "Alfalfa")),
        "lag_4w":            lag_4w,
        "lag_13w":           lag_13w,
        "roll_4w_mean":      roll_4w_mean,
        "diesel_4w_avg":     _rolling_mean(dfs.get("diesel"), ["price", "gallon", "diesel"], 4, 4.65),
        "diesel_13w_avg":    _rolling_mean(dfs.get("diesel"), ["price", "gallon", "diesel"], 13, 4.65),
        "milk_price_cwt":    _safe_last(dfs.get("milk"),   ["price", "cwt", "milk"], 23.50),
        "cattle_on_feed_ca": _safe_last(dfs.get("cattle"), ["cattle", "feed", "head", "cap"], 510_000.0),
        "stocks_may":        _safe_last(dfs.get("stocks"), ["stocks_may", "stocks"], 980_000.0),
        "stocks_may_yoy":    _safe_last(dfs.get("stocks"), ["yoy", "year_over"], 0.0),
        "avg_allocation":    _safe_last(dfs.get("water"),  ["allocation", "avg_alloc"], 72.0),
        "drought_year":      _safe_last(dfs.get("nass"),   ["drought_year", "drought"], 0.0),
        "production_tons":   _safe_last(dfs.get("nass"),   ["production_tons", "production"], 8_200_000.0),
        "acres_harvested":   _safe_last(dfs.get("nass"),   ["acres_harvested", "acres"], 900_000.0),
        "yield_tons_per_acre": _safe_last(dfs.get("nass"), ["yield_tons", "yield"], 9.1),
        "alfalfa_share":     _safe_last(dfs.get("nass"),   ["alfalfa_share", "alfalfa"], 0.72),
        "is_alfalfa":        1.0,
        "is_delivered":      float(is_delivered),
        "is_dairy_buyer":    0.0,
        "is_large_square":   0.0,
        "has_quality_issue": 0.0,
    }

    row = {f: features.get(f, 0.0) for f in feature_names} if feature_names else features
    return pd.DataFrame([row])


def run_prediction(
    zip_code: str,
    grade: str,
    delivery: str,
    zip_map: dict,
    dfs: dict,
    bundle: dict,
) -> dict:
    today        = date.today()
    is_delivered = 1 if delivery == "Delivered" else 0

    region_raw     = zip_map.get(zip_code, zip_map.get(zip_code[:3] + "00", "central_valley"))
    region_display = REGION_DISPLAY.get(str(region_raw).lower(), str(region_raw).replace("_", " ").title())

    X     = build_feature_row(str(region_raw), grade, is_delivered, today, dfs, bundle)
    pred  = float(bundle["model"].predict(X)[0])

    lag_4w     = float(X["lag_4w"].iloc[0]) if "lag_4w" in X.columns else pred
    trend_pct  = (pred - lag_4w) / lag_4w * 100 if lag_4w else 0.0

    return {
        "price":       pred,
        "low":         pred - MODEL_MAE,
        "high":        pred + MODEL_MAE,
        "region":      region_display,
        "grade":       f"{grade} Alfalfa",
        "week_of":     today.strftime("%B %d, %Y"),
        "trend_pct":   trend_pct,
        "diesel_4w":   _rolling_mean(dfs.get("diesel"), ["price", "gallon", "diesel"], 4, 4.65),
        "milk_cwt":    _safe_last(dfs.get("milk"),   ["price", "cwt", "milk"], 23.50),
        "cattle_head": _safe_last(dfs.get("cattle"), ["cattle", "feed", "head", "cap"], 510_000.0),
    }


# ── UI components ─────────────────────────────────────────────────────────────

def _hero() -> None:
    st.markdown("""
    <div style="text-align:center;padding:52px 0 36px;">
        <div style="font-family:'Nunito',sans-serif;font-size:50px;font-weight:900;
                    color:#1C1C1E;letter-spacing:-1.5px;line-height:1;">
            HayDay<span style="color:#C17F3E;">.ai</span>
        </div>
        <div style="font-family:'Nunito Sans',sans-serif;font-size:17px;
                    color:#8B7355;margin-top:10px;font-style:italic;
                    letter-spacing:0.01em;">
            California hay prices, predicted.
        </div>
    </div>
    """, unsafe_allow_html=True)


def _result_card(r: dict) -> None:
    tp = r["trend_pct"]
    if tp > 0.1:
        arrow, arrow_color, trend_label = "↑", "#C17F3E", f"+{tp:.1f}% vs 4 weeks ago"
    elif tp < -0.1:
        arrow, arrow_color, trend_label = "↓", "#4A7C59", f"{tp:.1f}% vs 4 weeks ago"
    else:
        arrow, arrow_color, trend_label = "→", "#8B7355", "Flat vs 4 weeks ago"

    cattle_fmt = f"{r['cattle_head'] / 1_000:.0f}K head"
    diesel_fmt = f"${r['diesel_4w']:.2f}/gal"
    milk_fmt   = f"${r['milk_cwt']:.2f}/cwt"

    st.markdown(f"""
<div style="animation:fadeSlideIn 0.45s ease;">

  <!-- ── Main result card ── -->
  <div style="background:#FFFFFF;border-radius:20px;
              box-shadow:0 4px 28px rgba(0,0,0,0.08);
              padding:36px 36px 28px;margin-bottom:14px;">

    <!-- Price -->
    <div style="text-align:center;margin-bottom:2px;">
      <span style="font-family:'Nunito',sans-serif;font-size:76px;font-weight:900;
                   color:#1C1C1E;letter-spacing:-3px;line-height:1.0;">
        ${r['price']:.0f}
      </span>
      <span style="font-family:'Nunito Sans',sans-serif;font-size:22px;
                   color:#8B7355;margin-left:2px;">/ton</span>
    </div>

    <!-- Confidence band -->
    <div style="text-align:center;margin-bottom:30px;">
      <span style="font-family:'Nunito Sans',sans-serif;font-size:15px;color:#B0A090;">
        ${r['low']:.0f} &mdash; ${r['high']:.0f}/ton
      </span>
    </div>

    <!-- Rule -->
    <div style="height:1px;background:#F0EBE2;margin-bottom:26px;"></div>

    <!-- Meta grid -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px 28px;margin-bottom:26px;">
      <div>
        <div style="font-family:'Nunito',sans-serif;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:0.06em;color:#C0B09A;margin-bottom:5px;">
          Region
        </div>
        <div style="font-family:'Nunito Sans',sans-serif;font-size:15px;
                    font-weight:600;color:#1C1C1E;">{r['region']}</div>
      </div>
      <div>
        <div style="font-family:'Nunito',sans-serif;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:0.06em;color:#C0B09A;margin-bottom:5px;">
          Grade
        </div>
        <div style="font-family:'Nunito Sans',sans-serif;font-size:15px;
                    font-weight:600;color:#1C1C1E;">{r['grade']}</div>
      </div>
      <div>
        <div style="font-family:'Nunito',sans-serif;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:0.06em;color:#C0B09A;margin-bottom:5px;">
          Week of
        </div>
        <div style="font-family:'Nunito Sans',sans-serif;font-size:15px;
                    font-weight:600;color:#1C1C1E;">{r['week_of']}</div>
      </div>
      <div>
        <div style="font-family:'Nunito',sans-serif;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:0.06em;color:#C0B09A;margin-bottom:5px;">
          Trend
        </div>
        <div style="font-family:'Nunito Sans',sans-serif;font-size:15px;
                    font-weight:600;color:{arrow_color};">
          {arrow} {trend_label}
        </div>
      </div>
    </div>

    <!-- Disclaimer -->
    <div style="text-align:center;">
      <span style="font-family:'Nunito Sans',sans-serif;font-size:12px;
                   color:#C0B09A;font-style:italic;">
        &plusmn;${MODEL_MAE:.2f}/ton model accuracy
      </span>
    </div>
  </div>

  <!-- ── Stat chips ── -->
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:14px;">
    <div style="background:#FFFFFF;border-radius:16px;padding:18px 10px 14px;
                text-align:center;box-shadow:0 2px 12px rgba(0,0,0,0.06);">
      <div style="font-size:24px;margin-bottom:7px;">🐄</div>
      <div style="font-family:'Nunito',sans-serif;font-size:10px;font-weight:700;
                  text-transform:uppercase;letter-spacing:0.05em;color:#C0B09A;margin-bottom:5px;">
        Cattle on Feed
      </div>
      <div style="font-family:'Nunito',sans-serif;font-size:15px;
                  font-weight:800;color:#1C1C1E;">{cattle_fmt}</div>
    </div>
    <div style="background:#FFFFFF;border-radius:16px;padding:18px 10px 14px;
                text-align:center;box-shadow:0 2px 12px rgba(0,0,0,0.06);">
      <div style="font-size:24px;margin-bottom:7px;">⛽</div>
      <div style="font-family:'Nunito',sans-serif;font-size:10px;font-weight:700;
                  text-transform:uppercase;letter-spacing:0.05em;color:#C0B09A;margin-bottom:5px;">
        Diesel 4W Avg
      </div>
      <div style="font-family:'Nunito',sans-serif;font-size:15px;
                  font-weight:800;color:#1C1C1E;">{diesel_fmt}</div>
    </div>
    <div style="background:#FFFFFF;border-radius:16px;padding:18px 10px 14px;
                text-align:center;box-shadow:0 2px 12px rgba(0,0,0,0.06);">
      <div style="font-size:24px;margin-bottom:7px;">🥛</div>
      <div style="font-family:'Nunito',sans-serif;font-size:10px;font-weight:700;
                  text-transform:uppercase;letter-spacing:0.05em;color:#C0B09A;margin-bottom:5px;">
        Milk Price
      </div>
      <div style="font-family:'Nunito',sans-serif;font-size:15px;
                  font-weight:800;color:#1C1C1E;">{milk_fmt}</div>
    </div>
  </div>

</div>
""", unsafe_allow_html=True)


def _footer() -> None:
    st.markdown("""
    <div style="text-align:center;padding:28px 0 0;
                font-family:'Nunito Sans',sans-serif;font-size:12px;color:#C0B09A;">
        Powered by USDA AMS &middot; Open-Meteo &middot; NASS
    </div>
    """, unsafe_allow_html=True)


# ── App entry point ───────────────────────────────────────────────────────────

st.set_page_config(
    page_title="HayDay.ai",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

_ensure_files()

bundle  = load_model_bundle()
dfs     = load_support_data()
zip_map = load_zip_map()

if "step"   not in st.session_state:
    st.session_state.step   = "input"
if "result" not in st.session_state:
    st.session_state.result = None

_hero()

# ── Input screen ──────────────────────────────────────────────────────────────
if st.session_state.step == "input":

    with st.container(border=True):
        st.markdown("""
        <div style="font-family:'Nunito',sans-serif;font-size:19px;font-weight:800;
                    color:#1C1C1E;margin-bottom:4px;">
            Get your price estimate
        </div>
        <div style="font-family:'Nunito Sans',sans-serif;font-size:14px;
                    color:#8B7355;margin-bottom:20px;">
            Enter your ZIP, grade, and delivery preference.
        </div>
        """, unsafe_allow_html=True)

        zip_code = st.text_input(
            "ZIP Code",
            placeholder="e.g. 93230",
            max_chars=5,
            key="zip_input",
        )
        grade = st.selectbox(
            "Hay Grade",
            GRADE_OPTIONS,
            key="grade_input",
        )
        delivery = st.selectbox(
            "Delivery Preference",
            DELIVERY_OPTIONS,
            key="delivery_input",
        )

        clicked = st.button("Get Price", use_container_width=True)

    if clicked:
        if not zip_code or len(zip_code) != 5 or not zip_code.isdigit():
            st.error("Please enter a valid 5-digit California ZIP code.")
        elif bundle is None:
            st.error("Model is still loading — please refresh and try again.")
        else:
            placeholder = st.empty()
            with placeholder.container():
                st.markdown("""
                <div style="text-align:center;padding:64px 0 56px;">
                  <div style="font-size:80px;display:inline-block;
                              animation:spin 1s linear infinite;">🌾</div>
                  <p style="font-family:'Nunito Sans',sans-serif;color:#8B7355;
                            font-size:16px;margin-top:24px;letter-spacing:0.01em;">
                    Analyzing California hay market…
                  </p>
                </div>
                """, unsafe_allow_html=True)

                result = run_prediction(zip_code, grade, delivery, zip_map, dfs, bundle)
                time.sleep(5)

            placeholder.empty()
            st.session_state.result = result
            st.session_state.step   = "result"
            st.rerun()

# ── Result screen ─────────────────────────────────────────────────────────────
elif st.session_state.step == "result" and st.session_state.result:
    _result_card(st.session_state.result)

    if st.button("← Get Another Price", use_container_width=True, key="back-btn"):
        st.session_state.step   = "input"
        st.session_state.result = None
        st.rerun()

_footer()
