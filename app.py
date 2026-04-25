import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import joblib
import math
import json
import os
import hashlib
from datetime import datetime

st.set_page_config(
    page_title="HayDay.ai",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;500;600;700&family=Nunito+Sans:wght@300;400;600&display=swap');

*, html, body, [class*="css"] {
    font-family: "Nunito Sans", sans-serif;
    box-sizing: border-box;
}
.stApp { background: #F5F0E8; color: #1C1C1E; }
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 40px 20px 60px !important;
    max-width: 680px !important;
    margin: 0 auto;
}
.hay-logo {
    text-align: center;
    margin-bottom: 36px;
}
.hay-logo-mark {
    font-family: "Nunito", sans-serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #8B7355;
}
.hay-logo-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #C17F3E;
    margin: 0 8px;
    vertical-align: middle;
}
.hero {
    text-align: center;
    margin-bottom: 32px;
}
.hero-title {
    font-family: "Nunito", sans-serif;
    font-size: 32px;
    font-weight: 700;
    color: #1C1C1E;
    letter-spacing: -0.5px;
    line-height: 1.2;
    margin-bottom: 10px;
}
.hero-title em { font-style: normal; color: #C17F3E; }
.hero-sub {
    font-size: 15px;
    color: #6B6B6B;
    line-height: 1.6;
    max-width: 480px;
    margin: 0 auto;
}
.input-card {
    background: #FFFFFF;
    border-radius: 20px;
    padding: 28px;
    margin-bottom: 20px;
    box-shadow: 0 2px 20px rgba(0,0,0,0.06);
}
div[data-testid="stNumberInput"] input {
    background: #F5F0E8 !important;
    border: 1.5px solid #E5DDD0 !important;
    border-radius: 12px !important;
    color: #1C1C1E !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    padding: 12px 16px !important;
}
div[data-testid="stNumberInput"] input:focus {
    border-color: #C17F3E !important;
    box-shadow: 0 0 0 3px rgba(193,127,62,0.12) !important;
    outline: none !important;
}
div[data-testid="stTextInput"] input {
    background: #F5F0E8 !important;
    border: 1.5px solid #E5DDD0 !important;
    border-radius: 12px !important;
    color: #1C1C1E !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    padding: 12px 16px !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #C17F3E !important;
    box-shadow: 0 0 0 3px rgba(193,127,62,0.12) !important;
    outline: none !important;
}
div[data-testid="stSelectbox"] > div > div {
    background: #F5F0E8 !important;
    border: 1.5px solid #E5DDD0 !important;
    border-radius: 12px !important;
    color: #1C1C1E !important;
}
label {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #8B7355 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
.stCheckbox label {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #3C3C3E !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    opacity: 1 !important;
}
.stCheckbox span { color: #3C3C3E !important; opacity: 1 !important; }
.stCheckbox p {
    color: #3C3C3E !important;
    font-size: 14px !important;
    font-weight: 600 !important;
}
div[data-testid="stCheckbox"] label span p { color: #3C3C3E !important; }
.stButton > button {
    width: 100% !important;
    background: #C17F3E !important;
    color: #FFFFFF !important;
    font-family: "Nunito", sans-serif !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    padding: 15px !important;
    border-radius: 14px !important;
    border: none !important;
    margin-top: 6px !important;
    box-shadow: 0 4px 14px rgba(193,127,62,0.3) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: #A86A2E !important;
    transform: translateY(-1px) !important;
}
.verdict-card {
    border-radius: 20px;
    padding: 28px;
    margin-bottom: 16px;
    box-shadow: 0 2px 20px rgba(0,0,0,0.06);
    animation: fadeUp 0.35s ease;
}
@keyframes fadeUp {
    from { opacity:0; transform:translateY(12px); }
    to   { opacity:1; transform:translateY(0); }
}
.verdict-eyebrow {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 8px;
    opacity: 0.7;
}
.verdict-title {
    font-family: "Nunito", sans-serif;
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.3px;
    margin-bottom: 10px;
}
.verdict-body {
    font-size: 15px;
    line-height: 1.65;
    opacity: 0.85;
}
.action-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border-radius: 100px;
    font-family: "Nunito", sans-serif;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.04em;
    margin-top: 16px;
}
.stat-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 16px;
}
.stat-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}
.stat-label {
    font-size: 10px;
    font-weight: 700;
    color: #8B7355;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 6px;
}
.stat-value {
    font-family: "Nunito", sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: #1C1C1E;
}
.stat-sub { font-size: 11px; color: #8B8B8B; margin-top: 3px; }
.position-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 20px 22px;
    margin-bottom: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}
.position-label {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    font-weight: 600;
    color: #8B7355;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
}
.bar-track {
    background: #EDE8DE;
    border-radius: 8px;
    height: 8px;
    position: relative;
    margin-bottom: 6px;
}
.bar-fill { height: 8px; border-radius: 8px; position: relative; }
.bar-dot {
    position: absolute;
    right: -6px;
    top: -4px;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 3px solid #FFFFFF;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.bar-ends {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #8B8B8B;
    margin-top: 4px;
}
.forecast-note {
    border-radius: 14px;
    padding: 16px 18px;
    font-size: 14px;
    line-height: 1.6;
    margin-bottom: 16px;
}
.data-footer {
    text-align: center;
    font-size: 11px;
    color: #AEAEB2;
    line-height: 1.8;
    margin-top: 32px;
    padding-top: 20px;
    border-top: 1px solid #EDE8DE;
}
.auth-card {
    background: #FFFFFF;
    border-radius: 20px;
    padding: 32px;
    margin-bottom: 20px;
    box-shadow: 0 2px 20px rgba(0,0,0,0.06);
}
.auth-title {
    font-family: "Nunito", sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: #1C1C1E;
    margin-bottom: 6px;
}
.auth-sub {
    font-size: 14px;
    color: #6B6B6B;
    margin-bottom: 24px;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)

# ── Supabase auth ────────────────────────────────────────
import requests as _requests
import hashlib as _hashlib

def _sb():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except:
        import os as _os
        url = _os.environ.get("SUPABASE_URL","")
        key = _os.environ.get("SUPABASE_KEY","")
    headers = {
        "apikey":        key,
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation",
    }
    return url, headers

def hash_pw(pw):
    return _hashlib.sha256(pw.encode()).hexdigest()

def register_user(email, password, name, op_type, state):
    url, headers = _sb()
    r = _requests.get(
        f"{url}/rest/v1/users?email=eq.{email.lower()}&select=email",
        headers=headers)
    if r.status_code == 200 and len(r.json()) > 0:
        return False, "Email already registered"
    r = _requests.post(
        f"{url}/rest/v1/users", headers=headers,
        json={"email": email.lower(), "password_hash": hash_pw(password),
              "name": name, "operation_type": op_type, "state": state})
    if r.status_code in [200, 201]:
        return True, "Success"
    return False, f"Signup failed: {r.text[:100]}"

def login_user(email, password):
    url, headers = _sb()
    r = _requests.get(
        f"{url}/rest/v1/users?email=eq.{email.lower()}&select=*",
        headers=headers)
    if r.status_code != 200 or not r.json():
        return False, "Email not found"
    user = r.json()[0]
    if user["password_hash"] != hash_pw(password):
        return False, "Incorrect password"
    return True, user

def log_check(email):
    url, headers = _sb()
    r = _requests.get(
        f"{url}/rest/v1/users?email=eq.{email.lower()}&select=checks",
        headers=headers)
    if r.status_code == 200 and r.json():
        current = r.json()[0].get("checks") or 0
        _requests.patch(
            f"{url}/rest/v1/users?email=eq.{email.lower()}",
            headers=headers,
            json={"checks": current+1,
                  "last_check": datetime.now().isoformat()})

def track_unserved_zip(z):
    url, headers = _sb()
    r = _requests.get(
        f"{url}/rest/v1/unserved_zips?zip=eq.{z}&select=attempts",
        headers=headers)
    if r.status_code == 200 and r.json():
        attempts = r.json()[0].get("attempts", 1)
        _requests.patch(
            f"{url}/rest/v1/unserved_zips?zip=eq.{z}",
            headers=headers,
            json={"attempts": attempts+1,
                  "last_seen": datetime.now().isoformat()})
    else:
        _requests.post(
            f"{url}/rest/v1/unserved_zips", headers=headers,
            json={"zip": z, "attempts": 1})

# ── Freight helpers ───────────────────────────────────────

def get_current_diesel():
    try:
        df = pd.read_csv("diesel_prices.csv")
        df["date"] = pd.to_datetime(df["date"])
        return float(df.sort_values("date", ascending=False).iloc[0]["diesel_price"])
    except Exception:
        return 4.50

def update_diesel_price(api_key):
    try:
        resp = _requests.get(
            "https://api.eia.gov/v2/petroleum/pri/gnd/data/",
            params={
                "api_key":              api_key,
                "frequency":            "weekly",
                "data[0]":              "value",
                "facets[duoarea][]":    "R5XCA",
                "facets[product][]":    "EPD2DXL0",
                "sort[0][column]":      "period",
                "sort[0][direction]":   "desc",
                "length":               2,
            },
            timeout=10,
        )
        resp.raise_for_status()
        records = resp.json()["response"]["data"]
        if not records:
            return get_current_diesel()

        latest_date  = records[0]["period"]
        latest_price = float(records[0]["value"])

        try:
            df = pd.read_csv("diesel_prices.csv")
            df["date"] = pd.to_datetime(df["date"])
            if latest_date not in df["date"].astype(str).values:
                new_row = pd.DataFrame([{"date": latest_date, "diesel_price": latest_price,
                                         "diesel_4w_avg": None, "diesel_13w_avg": None,
                                         "diesel_wow_chg": None}])
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv("diesel_prices.csv", index=False)
        except Exception:
            pass

        return latest_price
    except Exception:
        return get_current_diesel()

def get_driving_distance(origin_zip, delivery_zip, api_key):
    try:
        resp = _requests.get(
            "https://maps.googleapis.com/maps/api/distancematrix/json",
            params={
                "origins":      f"{origin_zip}, CA, USA",
                "destinations": f"{delivery_zip}, CA, USA",
                "units":        "imperial",
                "key":          api_key,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "OK":
            return {"miles": None, "method": "error", "valid": False,
                    "message": data.get("status", "API error")}
        element = data["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            return {"miles": None, "method": "error", "valid": False,
                    "message": element.get("status", "Route not found")}
        miles = round(element["distance"]["value"] * 0.000621371, 1)
        return {
            "miles":               miles,
            "method":              "google_maps",
            "valid":               True,
            "origin_address":      data["origin_addresses"][0],
            "destination_address": data["destination_addresses"][0],
        }
    except Exception as e:
        return {"miles": None, "method": "error", "valid": False, "message": str(e)}

def calculate_freight(miles, volume_tons, diesel_price):
    if volume_tons <= 0:
        return {"valid": False, "message": "Enter volume to calculate freight"}
    if miles is None:
        return {"valid": False, "message": "Could not calculate distance"}
    base_total      = max(600.00, miles * 5.00)
    fuel_surcharge  = max(0, round((diesel_price - 3.50) * 0.15 * miles, 2))
    total_freight   = base_total + fuel_surcharge
    freight_per_ton = total_freight / volume_tons
    return {
        "valid":           True,
        "miles":           miles,
        "base_total":      round(base_total, 2),
        "fuel_surcharge":  fuel_surcharge,
        "total_freight":   round(total_freight, 2),
        "freight_per_ton": round(freight_per_ton, 2),
        "diesel_price":    diesel_price,
    }

REGION_COORDS = {
    "Southeast":                  (32.8478, -115.5631),
    "Central San Joaquin Valley": (36.7468, -119.7726),
    "North San Joaquin Valley":   (37.3382, -120.4830),
    "Sacramento Valley":          (38.5816, -121.4944),
    "North Inter-Mountains":      (41.1765, -121.9553),
    "Colorado":                   (38.8339, -104.8214),
    "Oregon":                     (44.9429, -123.0351),
    "Idaho":                      (43.6150, -116.2023),
    "Montana":                    (46.8797, -110.3626),
}

CA_VALID_REGIONS = [
    "Central San Joaquin Valley",
    "North San Joaquin Valley",
    "Sacramento Valley",
    "North Inter-Mountains",
    "Southeast",
]

QUALITY_MATCH = {
    "Supreme":  ["Supreme", "Premium/Supreme"],
    "Premium":  ["Premium", "Good/Premium", "Premium/Supreme"],
    "Good":     ["Good", "Fair/Good", "Good/Premium"],
    "Fair":     ["Fair", "Fair/Good"],
    "Utility":  ["Utility"],
}

def filter_by_quality(df, quality):
    matches = QUALITY_MATCH.get(quality, [quality])
    return df[df["quality"].isin(matches)]

def haversine_miles(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi    = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return round(2 * R * math.asin(math.sqrt(a)), 1)

def get_region_coords_for_zip(zip_code, zip_to_region_map):
    region = zip_to_region_map.get(zip_code)
    if region and region in REGION_COORDS:
        return REGION_COORDS[region]
    return None

def get_driving_distance_coords(origin_coords, delivery_zip, api_key):
    try:
        lat, lng = origin_coords
        resp = _requests.get(
            "https://maps.googleapis.com/maps/api/distancematrix/json",
            params={
                "origins":      f"{lat},{lng}",
                "destinations": f"{delivery_zip}, CA, USA",
                "units":        "imperial",
                "key":          api_key,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "OK":
            return {"miles": None, "valid": False}
        element = data["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            return {"miles": None, "valid": False}
        return {"miles": round(element["distance"]["value"] * 0.000621371, 1), "valid": True}
    except Exception:
        return {"miles": None, "valid": False}

def find_cheaper_sources(
    delivery_zip, quoted_price, quoted_quality,
    is_alfalfa, df_prices, diesel_price,
    google_maps_key, zip_to_region_map, volume_tons,
):
    cutoff   = df_prices["date"].max() - pd.Timedelta(weeks=13)
    recent   = df_prices[df_prices["date"] >= cutoff].copy()
    if is_alfalfa and "is_alfalfa" in recent.columns:
        recent = recent[recent["is_alfalfa"] == 1]
    quality_data = filter_by_quality(recent, quoted_quality)
    if len(quality_data) < 3:
        quality_data = recent

    region_prices = (
        quality_data.groupby("region")["price_avg"]
        .agg(avg_fob="mean", count="count")
        .reset_index()
    )
    region_prices = region_prices[region_prices["count"] >= 3]

    delivery_coords = get_region_coords_for_zip(delivery_zip, zip_to_region_map)

    results = []
    for _, row in region_prices.iterrows():
        region  = row["region"]
        avg_fob = round(float(row["avg_fob"]), 2)
        if region not in REGION_COORDS:
            continue
        origin_coords = REGION_COORDS[region]
        if google_maps_key:
            dr = get_driving_distance_coords(origin_coords, delivery_zip, google_maps_key)
            miles = dr["miles"] if dr["valid"] else None
        else:
            miles = haversine_miles(origin_coords, delivery_coords) if delivery_coords else None
        if miles is None:
            continue
        fr = calculate_freight(miles, volume_tons, diesel_price)
        if not fr["valid"]:
            continue
        delivered_est    = round(avg_fob + fr["freight_per_ton"], 2)
        savings_per_ton  = round(quoted_price - delivered_est, 2)
        if savings_per_ton <= 0:
            continue
        results.append({
            "region":          region,
            "avg_fob":         avg_fob,
            "miles":           miles,
            "freight_per_ton": fr["freight_per_ton"],
            "delivered_est":   delivered_est,
            "savings_per_ton": savings_per_ton,
            "count":           int(row["count"]),
        })

    results.sort(key=lambda x: x["delivered_est"])
    return results[:3]

def log_quote_check(email, zip_code, region, quoted_price,
                    market_avg, verdict, volume):
    url, headers = _sb()
    _requests.post(
        f"{url}/rest/v1/quote_checks", headers=headers,
        json={"email": email, "zip_code": zip_code,
              "region": region, "quoted_price": float(quoted_price),
              "market_avg": round(float(market_avg), 2),
              "verdict": verdict,
              "volume": int(volume) if volume > 0 else None})

# ── Session state  ─────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in  = False
    st.session_state.user_email = ""
    st.session_state.user_name  = ""
    st.session_state.auth_mode  = "login"

# ── Load data ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data():
    df = pd.read_csv("california_hay_prices.csv")
    df["date"]   = pd.to_datetime(df["date"])
    df["region"] = df["region"].astype(str).str.strip()
    df["state"]  = df["state"].astype(str).str.strip()
    df = df[~df["region"].isin(["nan","None",""])]
    return df

@st.cache_resource
def load_model():
    try:
        return joblib.load("models/xgboost_enriched.pkl")
    except:
        return None

df_prices = load_data()
model_pkg = load_model()
QUALITIES = ["Supreme","Premium","Good","Fair","Utility"]

# ── Logo ──────────────────────────────────────────────────
st.markdown("""
<div class="hay-logo">
  <div class="hay-logo-mark">
    HayDay.ai <span class="hay-logo-dot"></span> Quote Checker
  </div>
</div>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-title">Was your quote <em>fair?</em></div>
  <div class="hero-sub">
    Enter the price your broker quoted.
    Get an instant read on whether it's a good deal
    and whether to buy now or wait.
  </div>
</div>
""", unsafe_allow_html=True)

# ── Auth gate ─────────────────────────────────────────────
if not st.session_state.logged_in:
    col_l, col_r = st.columns(2)
    with col_l:
        if st.button("Sign In",
                     type="primary" if st.session_state.auth_mode=="login" else "secondary",
                     use_container_width=True):
            st.session_state.auth_mode = "login"
            st.rerun()
    with col_r:
        if st.button("Create Account",
                     type="primary" if st.session_state.auth_mode=="signup" else "secondary",
                     use_container_width=True):
            st.session_state.auth_mode = "signup"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.auth_mode == "login":
        st.markdown('''<div class="auth-card">
          <div class="auth-title">Welcome back</div>
          <div class="auth-sub">Sign in to check your hay quote</div>
        </div>''', unsafe_allow_html=True)
        with st.form("login_form"):
            login_email    = st.text_input("Email address", placeholder="you@email.com")
            login_password = st.text_input("Password", type="password")
            login_submit   = st.form_submit_button("Sign In →", use_container_width=True)
        if login_submit:
            if not login_email or not login_password:
                st.error("Please fill in all fields")
            else:
                success, result = login_user(login_email, login_password)
                if success:
                    st.session_state.logged_in  = True
                    st.session_state.user_email = login_email
                    st.session_state.user_name  = result["name"]
                    st.rerun()
                else:
                    st.error(result)
    else:
        st.markdown('''<div class="auth-card">
          <div class="auth-title">Create your free account</div>
          <div class="auth-sub">Get instant market intelligence on every hay quote</div>
        </div>''', unsafe_allow_html=True)
        with st.form("signup_form"):
            col1, col2 = st.columns(2)
            with col1:
                signup_name  = st.text_input("Your name", placeholder="John Smith")
            with col2:
                signup_email = st.text_input("Email address", placeholder="you@email.com")
            col3, col4 = st.columns(2)
            with col3:
                signup_password = st.text_input("Password", type="password",
                                                placeholder="Min 6 characters")
            with col4:
                signup_op = st.selectbox("Operation type", [
                    "Dairy","Beef/Cattle","Horse","Hay Broker",
                    "Feed Store","Export","Other"
                ])
            signup_state = st.selectbox("Your state", [
                "California","Oregon","Idaho","Washington",
                "Colorado","Montana","Nevada","Arizona","Other"
            ])
            signup_submit = st.form_submit_button(
                "Create Free Account →", use_container_width=True
            )
        if signup_submit:
            if not signup_name or not signup_email or not signup_password:
                st.error("Please fill in all fields")
            elif len(signup_password) < 6:
                st.error("Password must be at least 6 characters")
            elif "@" not in signup_email:
                st.error("Please enter a valid email address")
            else:
                success, msg = register_user(
                    signup_email, signup_password,
                    signup_name, signup_op, signup_state
                )
                if success:
                    st.session_state.logged_in  = True
                    st.session_state.user_email = signup_email
                    st.session_state.user_name  = signup_name
                    st.rerun()
                else:
                    st.error(msg)
    st.stop()

# ── Logged in header ──────────────────────────────────────
col_w, col_o = st.columns([4,1])
with col_w:
    st.markdown(f"""
    <div style="font-size:13px;color:#8B7355;margin-bottom:16px;">
      👋 Welcome back, <strong style="color:#1C1C1E;">
      {st.session_state.user_name}</strong>
    </div>
    """, unsafe_allow_html=True)
with col_o:
    if st.button("Sign out", use_container_width=True):
        st.session_state.logged_in  = False
        st.session_state.user_email = ""
        st.session_state.user_name  = ""
        st.rerun()


# ── Market comparison helpers ─────────────────────────────
MIN_RECORDS = 3

def calc_stats(data):
    return (
        data["price_avg"].mean(),
        data["price_avg"].min(),
        data["price_avg"].max(),
        len(data),
    )

def get_market_comparison(df, quoted_region, quoted_quality,
                          is_alfalfa, is_delivered):
    ca_data = df[df["state"] == "California"].copy()

    def apply_filters(data, weeks):
        cutoff = data["date"].max() - pd.Timedelta(weeks=weeks)
        result = data[data["date"] >= cutoff].copy()
        if is_alfalfa and "is_alfalfa" in result.columns:
            sub = result[result["is_alfalfa"] == 1]
            if len(sub) >= MIN_RECORDS: result = sub
        if is_delivered and "is_delivered" in result.columns:
            sub = result[result["is_delivered"] == 1]
            if len(sub) >= MIN_RECORDS: result = sub
        return result

    def stats_dict(data, label, time_label):
        return {
            "market_avg":  round(data["price_avg"].mean(), 1),
            "market_lo":   round(data["price_avg"].min(),  1),
            "market_hi":   round(data["price_avg"].max(),  1),
            "n_trades":    len(data),
            "data_label":  label,
            "time_label":  time_label,
        }

    for weeks in [4, 8, 13, 26]:
        base  = apply_filters(ca_data[ca_data["region"] == quoted_region], weeks)
        qdata = filter_by_quality(base, quoted_quality)
        if len(qdata) >= MIN_RECORDS:
            return stats_dict(
                qdata,
                f"{quoted_quality} · {quoted_region}",
                f"last {weeks} weeks",
            )

    base = apply_filters(ca_data[ca_data["region"] == quoted_region], 13)
    if len(base) >= MIN_RECORDS:
        return stats_dict(
            base,
            f"{quoted_region} · all grades",
            "last 13 weeks — grade data limited",
        )

    base  = apply_filters(ca_data[ca_data["region"].isin(CA_VALID_REGIONS)], 13)
    qdata = filter_by_quality(base, quoted_quality)
    if len(qdata) >= MIN_RECORDS:
        return stats_dict(
            qdata,
            f"{quoted_quality} · CA regional avg",
            "last 13 weeks — limited local data",
        )

    base = apply_filters(ca_data[ca_data["region"].isin(CA_VALID_REGIONS)], 13)
    if len(base) >= MIN_RECORDS:
        return stats_dict(
            base,
            "CA regional avg · all grades",
            "last 13 weeks — limited local data",
        )

    return None


# ── Mobile-first overrides ────────────────────────────────
st.markdown("""
<style>
.main .block-container { max-width: 460px !important; padding-top: 1rem; }
.stButton > button {
    min-height: 52px; font-size: 16px; border-radius: 14px;
    font-weight: 700; font-family: 'Nunito Sans', sans-serif;
}
.stButton > button[kind="primary"] {
    background: #C17F3E !important; border-color: #C17F3E !important;
    color: #FFFFFF !important;
}
.stNumberInput input, .stTextInput input {
    min-height: 48px; font-size: 16px; border-radius: 12px;
}
div[data-baseweb="input"] { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# ── Quote-checker step state ──────────────────────────────
_qc_defaults = {
    "qc_step":     1,
    "qc_quality":  None,
    "qc_alfalfa":  True,
    "qc_bales":    512,
    "qc_lbs":      88,
    "qc_fob":      215.0,
    "qc_freight":  1900.0,
    "qc_unloading":0.0,
    "qc_zip":      "",
    "qc_logged":   False,
}
for _k, _v in _qc_defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

def qc_restart():
    for k in list(_qc_defaults.keys()):
        st.session_state[k] = _qc_defaults[k]

# Progress dots
_total_steps = 4
_current     = st.session_state.qc_step
_dots = "".join(
    f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
    f'margin:0 5px;background:{("#C17F3E" if i <= _current else "#E5DDD0")};"></span>'
    for i in range(1, _total_steps + 1)
)
st.markdown(
    f'<div style="text-align:center;margin:6px 0 18px;">{_dots}'
    f'<div style="font-size:11px;color:#8B7355;text-transform:uppercase;'
    f'letter-spacing:0.15em;margin-top:8px;font-weight:700;">'
    f'Step {_current} of {_total_steps}</div></div>',
    unsafe_allow_html=True,
)

# ── STEP 1 — Grade ────────────────────────────────────────
if st.session_state.qc_step == 1:
    st.markdown(
        '<div style="font-family:Nunito,sans-serif;font-size:22px;font-weight:800;'
        'color:#1C1C1E;margin-bottom:6px;">What grade are you buying?</div>'
        '<div style="font-size:14px;color:#8B7355;margin-bottom:18px;">'
        'Tap to select. Toggle alfalfa first if needed.</div>',
        unsafe_allow_html=True,
    )

    st.session_state.qc_alfalfa = st.toggle(
        "🌿  Pure Alfalfa", value=st.session_state.qc_alfalfa,
    )

    st.markdown(
        '<div style="margin-top:18px;font-size:11px;color:#8B7355;'
        'text-transform:uppercase;font-weight:700;letter-spacing:0.1em;'
        'margin-bottom:10px;">Quality grade</div>',
        unsafe_allow_html=True,
    )

    for _q in QUALITIES:
        if st.button(_q, key=f"qc_grade_{_q}", use_container_width=True):
            st.session_state.qc_quality = _q
            st.session_state.qc_step    = 2
            st.session_state.qc_logged  = False
            st.rerun()

# ── STEP 2 — Volume ───────────────────────────────────────
elif st.session_state.qc_step == 2:
    st.markdown(
        '<div style="font-family:Nunito,sans-serif;font-size:22px;font-weight:800;'
        'color:#1C1C1E;margin-bottom:6px;">How many bales?</div>'
        '<div style="font-size:14px;color:#8B7355;margin-bottom:18px;">'
        'Bale count and weight per bale.</div>',
        unsafe_allow_html=True,
    )

    _bales = st.number_input(
        "Number of bales",
        min_value=1, max_value=10000,
        value=int(st.session_state.qc_bales), step=1,
    )
    _lbs = st.number_input(
        "Lbs per bale",
        min_value=50, max_value=150,
        value=int(st.session_state.qc_lbs), step=1,
    )
    _tons = (_bales * _lbs) / 2000

    st.markdown(f"""
<div style="background:#FFFFFF;border-radius:18px;padding:20px;margin:14px 0;
            text-align:center;box-shadow:0 2px 14px rgba(0,0,0,0.05);">
  <div style="font-size:11px;color:#8B7355;text-transform:uppercase;
              font-weight:700;letter-spacing:0.1em;">Total Volume</div>
  <div style="font-size:34px;font-weight:800;color:#C17F3E;margin-top:6px;
              line-height:1;">{_tons:.2f} tons</div>
  <div style="font-size:13px;color:#8B7355;margin-top:6px;">
    {_bales} bales × {_lbs} lbs
  </div>
</div>
""", unsafe_allow_html=True)

    cb1, cb2 = st.columns(2)
    with cb1:
        if st.button("← Back", key="qc_back_2", use_container_width=True):
            st.session_state.qc_step = 1
            st.rerun()
    with cb2:
        if st.button("Next →", key="qc_next_2", use_container_width=True, type="primary"):
            st.session_state.qc_bales = int(_bales)
            st.session_state.qc_lbs   = int(_lbs)
            st.session_state.qc_step  = 3
            st.rerun()

# ── STEP 3 — Price & costs ────────────────────────────────
elif st.session_state.qc_step == 3:
    st.markdown(
        '<div style="font-family:Nunito,sans-serif;font-size:22px;font-weight:800;'
        'color:#1C1C1E;margin-bottom:6px;">Price & freight</div>'
        '<div style="font-size:14px;color:#8B7355;margin-bottom:18px;">'
        'FOB price, your actual freight, and where it\'s going.</div>',
        unsafe_allow_html=True,
    )

    _fob = st.number_input(
        "FOB price ($/ton)",
        min_value=50.0, max_value=800.0,
        value=float(st.session_state.qc_fob), step=5.0,
    )
    _freight = st.number_input(
        "Actual freight total ($)",
        min_value=0.0, max_value=20000.0,
        value=float(st.session_state.qc_freight), step=50.0,
        help="Your carrier's actual quote — total dollars for the load",
    )
    _unl = st.number_input(
        "Unloading ($) — optional",
        min_value=0.0, max_value=5000.0,
        value=float(st.session_state.qc_unloading), step=10.0,
    )
    _zip = st.text_input(
        "Delivery zip (5 digits)",
        value=st.session_state.qc_zip, max_chars=5,
        placeholder="e.g. 93706",
    )

    cb1, cb2 = st.columns(2)
    with cb1:
        if st.button("← Back", key="qc_back_3", use_container_width=True):
            st.session_state.qc_step = 2
            st.rerun()
    with cb2:
        if st.button("Check It →", key="qc_check", use_container_width=True, type="primary"):
            st.session_state.qc_fob       = float(_fob)
            st.session_state.qc_freight   = float(_freight)
            st.session_state.qc_unloading = float(_unl)
            st.session_state.qc_zip       = _zip.strip() if _zip else ""
            st.session_state.qc_step      = 4
            st.session_state.qc_logged    = False
            log_check(st.session_state.user_email)
            st.rerun()

# ── STEP 4 — Results ──────────────────────────────────────
elif st.session_state.qc_step == 4:
    quoted_quality   = st.session_state.qc_quality
    is_alfalfa_input = st.session_state.qc_alfalfa
    bale_count       = st.session_state.qc_bales
    lbs_per_bale     = st.session_state.qc_lbs
    fob_price        = st.session_state.qc_fob
    freight_total    = st.session_state.qc_freight
    unloading        = st.session_state.qc_unloading
    zip_clean        = st.session_state.qc_zip

    volume_tons = (bale_count * lbs_per_bale) / 2000

    # Validate zip
    if not zip_clean or len(zip_clean) != 5 or not zip_clean.isdigit():
        st.warning("We need a valid 5-digit delivery zip to check your quote.")
        if st.button("← Back to fix", use_container_width=True):
            st.session_state.qc_step = 3
            st.rerun()
        st.stop()

    # Zip → region
    import json as _json
    _zip_map = {}
    if os.path.exists("zip_to_region.json"):
        with open("zip_to_region.json") as _zf:
            _zip_map = _json.load(_zf)
    quoted_region = _zip_map.get(zip_clean, None)

    if not quoted_region:
        track_unserved_zip(zip_clean)
        st.markdown(f"""
<div style="background:#FFFFFF;border-radius:20px;padding:28px 24px;text-align:center;
            box-shadow:0 2px 14px rgba(0,0,0,0.06);">
  <div style="font-size:36px;margin-bottom:10px;">🌾</div>
  <div style="font-family:Nunito,sans-serif;font-size:18px;font-weight:800;
              color:#1C1C1E;margin-bottom:8px;">
    Not in coverage yet
  </div>
  <div style="font-size:14px;color:#6B6B6B;line-height:1.6;">
    Zip <strong>{zip_clean}</strong> isn't in our area yet. We've saved it
    and will email <strong>{st.session_state.user_email}</strong> when we expand.
  </div>
</div>
""", unsafe_allow_html=True)
        if st.button("Try another zip", use_container_width=True):
            st.session_state.qc_step = 3
            st.rerun()
        st.stop()

    # Market comparison (FOB market)
    _mc = get_market_comparison(
        df_prices, quoted_region, quoted_quality, is_alfalfa_input, False,
    )
    if _mc is None:
        st.warning("Not enough market data for this region yet.")
        if st.button("Start Over", use_container_width=True):
            qc_restart()
            st.rerun()
        st.stop()

    market_avg = _mc["market_avg"]
    market_lo  = _mc["market_lo"]
    market_hi  = _mc["market_hi"]
    n_trades   = _mc["n_trades"]
    data_label = _mc["data_label"]
    time_label = _mc["time_label"]

    # Cost computation
    freight_per_ton           = freight_total / volume_tons if volume_tons > 0 else 0.0
    full_load_freight_per_ton = freight_total / 40.0       if freight_total > 0 else 0.0
    hay_cost                  = fob_price * volume_tons
    total_cost                = hay_cost + freight_total + unloading
    landed_per_ton            = total_cost / volume_tons   if volume_tons > 0 else 0.0
    landed_per_bale           = total_cost / bale_count    if bale_count   > 0 else 0.0
    market_baseline           = market_avg + full_load_freight_per_ton
    landed_diff               = landed_per_ton - market_baseline
    landed_diff_pct           = (landed_diff / market_baseline * 100) if market_baseline else 0.0

    # Verdict
    if landed_diff_pct > 10:
        title  = "Overpriced"
        action = "Negotiate or Walk Away"
        bg     = "#FFF2F0"; border = "#FFD5CC"; color = "#C0392B"
    elif landed_diff_pct > 5:
        title  = "Slightly High"
        action = "Try to Negotiate"
        bg     = "#FFFBF0"; border = "#FFE9A0"; color = "#B07D00"
    elif landed_diff_pct >= -5:
        title  = "Fair Price"
        action = "Good to Go"
        bg     = "#F0FAF4"; border = "#B8E6C8"; color = "#1A7A40"
    else:
        title  = "Below Market"
        action = "Buy Now"
        bg     = "#F0FAF4"; border = "#B8E6C8"; color = "#1A7A40"

    total_savings = -landed_diff * volume_tons
    if total_savings > 1:
        savings_label = f"Save <strong>${total_savings:,.0f}</strong> total"
    elif abs(total_savings) > 1:
        savings_label = f"Overpay <strong>${abs(total_savings):,.0f}</strong> total"
    else:
        savings_label = ""

    # Hero verdict badge
    st.markdown(f"""
<div style="background:{bg};border:2px solid {border};border-radius:24px;
            padding:30px 22px;text-align:center;margin-bottom:14px;
            box-shadow:0 4px 24px rgba(0,0,0,0.08);">
  <div style="font-size:13px;font-weight:800;color:{color};text-transform:uppercase;
              letter-spacing:0.15em;">{title}</div>
  <div style="font-size:48px;font-weight:800;color:{color};margin:14px 0 4px;line-height:1;">
    ${landed_per_ton:.2f}
  </div>
  <div style="font-size:13px;color:{color};margin-bottom:6px;font-weight:600;">
    landed / ton
  </div>
  <div style="font-size:14px;color:{color};margin-bottom:18px;">
    ${landed_per_bale:.2f} per bale · {volume_tons:.2f} tons
  </div>
  <div style="background:{color};color:#FFFFFF;border-radius:16px;padding:14px 16px;
              font-weight:800;font-size:16px;letter-spacing:0.02em;">
    {action}
  </div>
  {f'<div style="margin-top:14px;font-size:14px;color:{color};">{savings_label}</div>' if savings_label else ""}
</div>
""", unsafe_allow_html=True)

    # vs Market card
    _arrow      = "✅ BELOW MARKET" if landed_diff <= 0 else (
                   "⚠️ ABOVE MARKET" if landed_diff_pct <= 10 else "❌ OVERPRICED")
    _diff_color = "#1A7A40" if landed_diff <= 0 else (
                   "#B07D00" if landed_diff_pct <= 10 else "#C0392B")
    st.markdown(f"""
<div style="background:#FFFFFF;border-radius:20px;padding:20px;margin-bottom:14px;
            box-shadow:0 2px 12px rgba(0,0,0,0.05);border-left:4px solid {_diff_color};">
  <div style="font-size:11px;font-weight:700;color:#8B7355;text-transform:uppercase;
              letter-spacing:0.1em;margin-bottom:12px;">vs Market</div>
  <div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:6px;">
    <span>Your landed:</span><span><strong>${landed_per_ton:.2f}/ton</strong></span>
  </div>
  <div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:6px;">
    <span>Market estimate:</span><span><strong>${market_baseline:.2f}/ton</strong></span>
  </div>
  <div style="display:flex;justify-content:space-between;font-size:15px;font-weight:800;
              color:{_diff_color};margin-top:8px;border-top:1px solid #E5DDD0;padding-top:8px;">
    <span>Difference:</span><span>${landed_diff:+.2f}/ton</span>
  </div>
  <div style="font-size:12px;color:{_diff_color};font-weight:700;margin-top:6px;
              text-align:right;">{_arrow}</div>
  <div style="font-size:11px;color:#8B7355;margin-top:10px;">
    {data_label} · {time_label} · {n_trades} trades
  </div>
</div>
""", unsafe_allow_html=True)

    # Cost breakdown card
    _unl_line = (
        f'<div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:4px;">'
        f'<span>Unloading:</span><span><strong>${unloading:,.2f}</strong></span></div>'
    ) if unloading > 0 else ""
    _freight_line = (
        f'<div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:4px;">'
        f'<span>Freight:</span><span><strong>${freight_total:,.2f}</strong> '
        f'<span style="color:#8B7355;font-size:12px;">(${freight_per_ton:.2f}/ton)</span></span></div>'
    ) if freight_total > 0 else ""
    st.markdown(f"""
<div style="background:#FFFFFF;border-radius:20px;padding:20px;margin-bottom:14px;
            box-shadow:0 2px 12px rgba(0,0,0,0.05);">
  <div style="font-size:11px;font-weight:700;color:#8B7355;text-transform:uppercase;
              letter-spacing:0.1em;margin-bottom:12px;">📦 Cost Breakdown</div>
  <div style="display:flex;justify-content:space-between;font-size:13px;color:#8B7355;margin-bottom:10px;">
    <span>Volume:</span>
    <span><strong style="color:#1C1C1E;">{volume_tons:.2f} tons ({bale_count} bales)</strong></span>
  </div>
  <div style="display:flex;justify-content:space-between;font-size:13px;color:#8B7355;margin-bottom:14px;">
    <span>FOB price:</span>
    <span><strong style="color:#1C1C1E;">${fob_price:.2f}/ton</strong></span>
  </div>
  <div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:4px;">
    <span>Hay cost:</span><span><strong>${hay_cost:,.2f}</strong></span>
  </div>
  {_freight_line}
  {_unl_line}
  <div style="border-top:1px solid #E5DDD0;margin:10px 0;"></div>
  <div style="display:flex;justify-content:space-between;font-size:15px;font-weight:700;">
    <span>TOTAL:</span><span>${total_cost:,.2f}</span>
  </div>
  <div style="display:flex;justify-content:space-between;font-size:18px;font-weight:800;
              color:#C17F3E;margin-top:6px;">
    <span>LANDED:</span><span>${landed_per_ton:.2f}/ton</span>
  </div>
  <div style="text-align:right;font-size:13px;color:#8B7355;margin-top:2px;">
    ${landed_per_bale:.2f}/bale
  </div>
</div>
""", unsafe_allow_html=True)

    # Partial load alert
    if volume_tons < 35 and freight_total > 0:
        _premium_per_ton = freight_per_ton - full_load_freight_per_ton
        _premium_total   = _premium_per_ton * volume_tons
        st.markdown(f"""
<div style="background:#FFFBF0;border:1.5px solid #FFE9A0;border-radius:18px;
            padding:18px 20px;margin-bottom:14px;color:#B07D00;">
  <div style="font-weight:800;font-size:15px;margin-bottom:8px;">
    ⚠️ Partial Load Premium
  </div>
  <div style="font-size:14px;line-height:1.7;">
    Your freight: <strong>${freight_per_ton:.2f}/ton</strong><br>
    Full load:    <strong>${full_load_freight_per_ton:.2f}/ton</strong> (at 40 tons)<br>
    Premium:      <strong>${_premium_per_ton:.2f}/ton extra</strong>
  </div>
  <div style="font-size:13px;margin-top:10px;color:#A06010;">
    Filling the truck saves <strong>${_premium_total:,.0f}</strong> on this load.
  </div>
</div>
""", unsafe_allow_html=True)

    # Forecast
    forecast_avg = market_avg
    forecast_dir = 0
    if model_pkg and quoted_region:
        try:
            model    = model_pkg["model"]
            features = model_pkg["features"]
            encoders = model_pkg["encoders"]
            r_df     = df_prices[
                (df_prices["state"]  == "California") &
                (df_prices["region"] == quoted_region)
            ].sort_values("date")
            prices  = r_df["price_avg"].values
            df_nass = pd.read_csv("nass_supply_data.csv")
            nass_row = df_nass.sort_values("year").iloc[[-1]]
            fdate   = pd.Timestamp.now() + pd.Timedelta(days=7)
            m, w, q = fdate.month, fdate.isocalendar()[1], (fdate.month-1)//3+1
            lag_4w  = float(np.mean(prices[-2:]))  if len(prices) >= 2  else float(prices[-1])
            lag_13w = float(np.mean(prices[-6:]))  if len(prices) >= 6  else lag_4w
            lag_26w = float(np.mean(prices[-13:])) if len(prices) >= 13 else lag_13w
            def _enc(name, val):
                le = encoders[name]
                v  = val if val in le.classes_ else le.classes_[0]
                return int(le.transform([v])[0])
            feat_row = {
                "month_sin": np.sin(2*np.pi*m/12),
                "month_cos": np.cos(2*np.pi*m/12),
                "week_sin":  np.sin(2*np.pi*w/52),
                "week_cos":  np.cos(2*np.pi*w/52),
                "quarter":   q,
                "region_enc":    _enc("region", quoted_region),
                "quality_enc":   _enc("quality", quoted_quality),
                "commodity_enc": _enc("commodity", "ALFALFA HAY"),
                "lag_4w":    lag_4w,
                "lag_13w":   lag_13w,
                "lag_26w":   lag_26w,
                "roll_4w_mean":  lag_4w,
                "roll_13w_mean": lag_13w,
                "production_tons":     float(nass_row["production_tons"].values[0]),
                "acres_harvested":     float(nass_row["acres_harvested"].values[0]),
                "yield_tons_per_acre": float(nass_row["yield_tons_per_acre"].values[0]),
                "alfalfa_share":       float(nass_row["alfalfa_share"].values[0]),
            }
            X = np.array([[feat_row.get(f, 0) for f in features]])
            forecast_avg = float(np.clip(model.predict(X)[0], 50, 800))
            forecast_dir = forecast_avg - market_avg
        except Exception:
            pass

    if forecast_dir > 8:
        fc_bg="#FFF8F0"; fc_border="#FFD9A8"; fc_color="#A06010"
        fc_text=f"📈 Prices forecast to <strong>rise ~${forecast_dir:.0f}/ton</strong> next 7 days. If this quote is fair, lock it in."
    elif forecast_dir < -8:
        fc_bg="#F0FAF4"; fc_border="#B8E6C8"; fc_color="#1A5C30"
        fc_text=f"📉 Prices forecast to <strong>drop ~${abs(forecast_dir):.0f}/ton</strong> next 7 days. Waiting may pay off."
    else:
        fc_bg="#F8F6F2"; fc_border="#E5DDD0"; fc_color="#6B6B6B"
        fc_text=f"→ Prices in {quoted_region} look stable next 7 days."

    st.markdown(f"""
<div style="background:{fc_bg};border:1.5px solid {fc_border};color:{fc_color};
            border-radius:16px;padding:16px 18px;font-size:14px;margin-bottom:14px;">
  {fc_text}
</div>
""", unsafe_allow_html=True)

    # Log once per result render
    if not st.session_state.qc_logged:
        try:
            log_quote_check(
                st.session_state.user_email, zip_clean, quoted_region,
                fob_price, market_avg, title, volume_tons,
            )
        except Exception:
            pass
        st.session_state.qc_logged = True

    # Start over
    if st.button("Start Over", use_container_width=True, type="primary"):
        qc_restart()
        st.rerun()

# ── Footer ────────────────────────────────────────────────
st.markdown("""
<div class="data-footer">
  USDA AMS · XGBoost forecast · MAE ±$17.59/ton<br>
  Market intelligence only — not financial advice
</div>
""", unsafe_allow_html=True)
