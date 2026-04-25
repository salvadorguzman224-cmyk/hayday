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

# ── Input form ────────────────────────────────────────────
st.markdown('<div class="input-card">', unsafe_allow_html=True)

# SECTION A — What are you buying?
st.markdown(
    '<div style="font-size:11px;font-weight:700;color:#8B7355;'
    'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">'
    'A · What are you buying?</div>',
    unsafe_allow_html=True,
)
colA1, colA2 = st.columns(2)
with colA1:
    quoted_quality = st.selectbox("Quality grade", options=QUALITIES, index=1)
with colA2:
    cutting = st.selectbox(
        "Cutting (optional)",
        options=["Unknown", "1st", "2nd", "3rd", "4th"], index=0,
    )
is_alfalfa_input = st.checkbox("🌿  Pure Alfalfa", value=True)

# SECTION B — Volume
st.markdown(
    '<div style="font-size:11px;font-weight:700;color:#8B7355;'
    'text-transform:uppercase;letter-spacing:0.1em;margin:14px 0 8px;">'
    'B · Volume</div>',
    unsafe_allow_html=True,
)
volume_type = st.radio(
    "Volume type", ["Tons", "Bales"], horizontal=True, label_visibility="collapsed",
)
if volume_type == "Tons":
    volume_tons  = float(st.number_input(
        "Volume (tons)", min_value=1.0, max_value=1000.0, value=22.0, step=0.5,
    ))
    bale_count   = 0
    lbs_per_bale = 0
else:
    colB1, colB2 = st.columns(2)
    with colB1:
        bale_count = int(st.number_input(
            "Number of bales", min_value=1, max_value=10000, value=512, step=1,
        ))
    with colB2:
        lbs_per_bale = int(st.number_input(
            "Lbs per bale", min_value=50, max_value=150, value=88, step=1,
        ))
    volume_tons = (bale_count * lbs_per_bale) / 2000
    st.markdown(
        f'<div style="font-size:13px;color:#8B7355;margin-top:-4px;">'
        f'{bale_count} bales × {lbs_per_bale} lbs = '
        f'<strong>{volume_tons:.2f} tons</strong></div>',
        unsafe_allow_html=True,
    )

# SECTION C — Price
st.markdown(
    '<div style="font-size:11px;font-weight:700;color:#8B7355;'
    'text-transform:uppercase;letter-spacing:0.1em;margin:14px 0 8px;">'
    'C · Price</div>',
    unsafe_allow_html=True,
)
price_type = st.radio(
    "Price type",
    ["FOB (at origin)", "Delivered (includes freight)"],
    horizontal=True, label_visibility="collapsed",
)
if price_type == "FOB (at origin)":
    fob_price_input       = float(st.number_input(
        "FOB price ($/ton)", min_value=50.0, max_value=800.0, value=215.0, step=5.0,
    ))
    delivered_price_input = 0.0
else:
    delivered_price_input = float(st.number_input(
        "Delivered price ($/ton)", min_value=50.0, max_value=800.0, value=280.0, step=5.0,
    ))
    fob_price_input       = 0.0

# SECTION D — Location
st.markdown(
    '<div style="font-size:11px;font-weight:700;color:#8B7355;'
    'text-transform:uppercase;letter-spacing:0.1em;margin:14px 0 8px;">'
    'D · Location</div>',
    unsafe_allow_html=True,
)
colz1, colz2 = st.columns(2)
with colz1:
    zip_input = st.text_input(
        "Delivery zip (your location)", placeholder="e.g. 93706", max_chars=5,
    )
with colz2:
    origin_zip_input = st.text_input(
        "Origin zip (where hay ships from)", placeholder="e.g. 95376", max_chars=5,
    )

# Zip → region
import json as _json
_zip_map = {}
if os.path.exists("zip_to_region.json"):
    with open("zip_to_region.json") as _zf:
        _zip_map = _json.load(_zf)

zip_clean          = zip_input.strip() if zip_input else ""
origin_zip_clean   = origin_zip_input.strip() if origin_zip_input else ""
auto_region        = _zip_map.get(zip_clean, None)
quoted_region      = None
zip_not_in_service = False

if zip_clean and len(zip_clean) == 5 and zip_clean.isdigit():
    if auto_region:
        quoted_region = auto_region
        st.markdown(f"""
        <div style="background:#F0FAF4;border:1.5px solid #B8E6C8;
                    border-radius:10px;padding:10px 14px;
                    margin-top:-4px;margin-bottom:8px;
                    font-size:13px;color:#1A7A40;">
          📍 <strong>{auto_region}</strong>
        </div>
        """, unsafe_allow_html=True)
    else:
        zip_not_in_service = True
        track_unserved_zip(zip_clean)
elif zip_clean and len(zip_clean) < 5:
    st.markdown("""
    <div style="background:#FFFBF0;border:1.5px solid #FFE9A0;
                border-radius:10px;padding:8px 14px;
                margin-top:-4px;font-size:13px;color:#B07D00;">
      Keep typing...
    </div>
    """, unsafe_allow_html=True)

# SECTION E — Actual costs (optional)
st.markdown(
    '<div style="font-size:11px;font-weight:700;color:#8B7355;'
    'text-transform:uppercase;letter-spacing:0.1em;margin:14px 0 8px;">'
    'E · Actual costs (optional)</div>',
    unsafe_allow_html=True,
)
colE1, colE2, colE3 = st.columns(3)
with colE1:
    actual_freight = float(st.number_input(
        "Freight ($)", min_value=0.0, max_value=20000.0, value=0.0, step=50.0,
        placeholder="e.g. 1900",
        help="Enter your carrier's actual quote — more accurate than our estimate",
    ))
with colE2:
    unloading = float(st.number_input(
        "Unloading ($)", min_value=0.0, max_value=5000.0, value=0.0, step=10.0,
        placeholder="e.g. 120",
    ))
with colE3:
    other_fees = float(st.number_input(
        "Other fees ($)", min_value=0.0, max_value=5000.0, value=0.0, step=10.0,
        placeholder="tarps, surcharge",
    ))

# Compatibility shims for downstream code
is_delivered_input = False
quoted_volume      = volume_tons
quoted_price       = fob_price_input if price_type == "FOB (at origin)" else delivered_price_input

check = st.button("Check My Quote →", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if check:
    log_check(st.session_state.user_email)

# ── Not in service ────────────────────────────────────────
if check and zip_not_in_service:
    st.markdown(f"""
    <div style="background:#FFFFFF;border-radius:20px;padding:32px;
                box-shadow:0 2px 20px rgba(0,0,0,0.06);
                text-align:center;margin-top:8px;">
      <div style="font-size:40px;margin-bottom:16px;">🌾</div>
      <div style="font-family:'Nunito',sans-serif;font-size:20px;
                  font-weight:700;color:#1C1C1E;margin-bottom:10px;">
        Not in our coverage area yet
      </div>
      <div style="font-size:15px;color:#6B6B6B;line-height:1.7;
                  max-width:380px;margin:0 auto 20px;">
        Zip code <strong>{zip_clean}</strong> isn't in our service area yet.
        We're expanding rapidly across Western states and will notify you
        as soon as your area is covered.
      </div>
      <div style="background:#F5F0E8;border-radius:12px;padding:16px;
                  max-width:320px;margin:0 auto;">
        <div style="font-size:12px;font-weight:700;color:#8B7355;
                    text-transform:uppercase;letter-spacing:0.08em;
                    margin-bottom:8px;">
          Get notified when we expand
        </div>
        <div style="font-size:13px;color:#3C3C3E;">
          We've saved your zip code. We'll email
          <strong>{st.session_state.user_email}</strong>
          when your area goes live.
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if check and not zip_clean:
    st.warning("Please enter your zip code to check your quote.")
    st.stop()

if check and quoted_region is None and not zip_not_in_service:
    st.warning("Please enter a valid 5-digit zip code.")
    st.stop()

# ── Market comparison ─────────────────────────────────────
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

    # Steps 1-4: same quality + same region, expanding time window
    for weeks in [4, 8, 13, 26]:
        base  = apply_filters(ca_data[ca_data["region"] == quoted_region], weeks)
        qdata = filter_by_quality(base, quoted_quality)
        if len(qdata) >= MIN_RECORDS:
            return stats_dict(
                qdata,
                f"{quoted_quality} · {quoted_region}",
                f"last {weeks} weeks",
            )

    # Step 5: all grades + same region + 13 weeks
    base = apply_filters(ca_data[ca_data["region"] == quoted_region], 13)
    if len(base) >= MIN_RECORDS:
        return stats_dict(
            base,
            f"{quoted_region} · all grades",
            "last 13 weeks — grade data limited",
        )

    # Step 6: same quality + all valid CA regions + 13 weeks
    base  = apply_filters(ca_data[ca_data["region"].isin(CA_VALID_REGIONS)], 13)
    qdata = filter_by_quality(base, quoted_quality)
    if len(qdata) >= MIN_RECORDS:
        return stats_dict(
            qdata,
            f"{quoted_quality} · CA regional avg",
            "last 13 weeks — limited local data",
        )

    # Step 7: all grades + all valid CA regions + 13 weeks
    base = apply_filters(ca_data[ca_data["region"].isin(CA_VALID_REGIONS)], 13)
    if len(base) >= MIN_RECORDS:
        return stats_dict(
            base,
            "CA regional avg · all grades",
            "last 13 weeks — limited local data",
        )

    return None

_mc_result = get_market_comparison(
    df_prices, quoted_region, quoted_quality,
    is_alfalfa_input, is_delivered_input,
)

if _mc_result is None:
    st.warning("Not enough market data for this region yet.")
    st.stop()

market_avg = _mc_result["market_avg"]
market_lo  = _mc_result["market_lo"]
market_hi  = _mc_result["market_hi"]
n_trades   = _mc_result["n_trades"]
data_label = _mc_result["data_label"]
time_label = _mc_result["time_label"]
diff       = quoted_price - market_avg
diff_pct   = diff / market_avg * 100
pct_rank   = max(0, min(100,
    (quoted_price - market_lo) / (market_hi - market_lo) * 100
    if market_hi > market_lo else 50
))

SEASONAL_CONTEXT = {
    1:  "January prices are typically elevated — winter stocks running low",
    2:  "February is historically the highest-price month of the year",
    3:  "March prices begin declining as first cutting approaches",
    4:  "April — first cutting imminent, prices softening",
    5:  "May — first cutting harvest, maximum supply, lowest prices",
    6:  "June — peak supply month, best time to buy",
    7:  "July prices rise as summer heat stresses second cutting",
    8:  "August — second cutting complete, prices stabilizing",
    9:  "September — third cutting underway, good supply available",
    10: "October prices begin rising as winter stocks build",
    11: "November — pre-winter buying season, prices climbing",
    12: "December — winter premium in effect, lock in supply now",
}
seasonal_note = SEASONAL_CONTEXT.get(datetime.now().month, "")

# ── Early freight calculation ──────────────────────────────
freight_valid   = False
freight_per_ton = 0.0
fob_equivalent  = float(quoted_price)
distance_miles  = None
_freight_data   = None
_freight_error  = None

if (check
        and origin_zip_clean
        and len(origin_zip_clean) == 5
        and origin_zip_clean.isdigit()):
    _gmaps_key = st.secrets.get("GOOGLE_MAPS_API_KEY", "")
    _diesel    = get_current_diesel()
    if _gmaps_key:
        with st.spinner("Calculating freight distance…"):
            _dist_r = get_driving_distance(origin_zip_clean, zip_clean, _gmaps_key)
    else:
        _dist_r = {"valid": False, "message": "Google Maps API key not configured"}
    if _dist_r["valid"]:
        _fr_r = calculate_freight(_dist_r["miles"], quoted_volume, _diesel)
        if _fr_r["valid"]:
            freight_valid   = True
            freight_per_ton = _fr_r["freight_per_ton"]
            fob_equivalent  = round(quoted_price - freight_per_ton, 2)
            distance_miles  = _dist_r["miles"]
            _freight_data   = {"dist": _dist_r, "freight": _fr_r, "diesel": _diesel}
        else:
            _freight_error = _fr_r.get("message", "Unknown error")
    else:
        _freight_error = _dist_r.get("message", "Unknown error")

# ── Cost computation ──────────────────────────────────────
_freight_estimate_total = (
    _freight_data["freight"]["total_freight"] if _freight_data else 0.0
)
freight_total   = actual_freight if actual_freight > 0 else _freight_estimate_total
freight_per_ton = (freight_total / volume_tons) if volume_tons > 0 else 0.0

if price_type == "FOB (at origin)":
    fob_price = fob_price_input
else:
    fob_price = delivered_price_input - freight_per_ton

quoted_price    = fob_price
fob_equivalent  = fob_price
total_other     = unloading + other_fees
hay_cost        = fob_price * volume_tons
total_cost      = hay_cost + freight_total + total_other
landed_per_ton  = total_cost / volume_tons if volume_tons > 0 else 0.0
landed_per_bale = (total_cost / bale_count) if bale_count > 0 else 0.0
unloading_per_ton = unloading / volume_tons if volume_tons > 0 else 0.0
other_per_ton     = other_fees / volume_tons if volume_tons > 0 else 0.0
full_load_freight_per_ton = freight_total / 40.0 if freight_total > 0 else 0.0

market_baseline = market_avg + full_load_freight_per_ton
landed_diff     = landed_per_ton - market_baseline
landed_diff_pct = (landed_diff / market_baseline * 100) if market_baseline else 0.0

# ── Forecast ──────────────────────────────────────────────
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
        lag_4w  = float(np.mean(prices[-2:])) if len(prices)>=2 else float(prices[-1])
        lag_13w = float(np.mean(prices[-6:])) if len(prices)>=6 else lag_4w
        lag_26w = float(np.mean(prices[-13:])) if len(prices)>=13 else lag_13w
        def enc(name, val):
            le = encoders[name]
            v  = val if val in le.classes_ else le.classes_[0]
            return int(le.transform([v])[0])
        feat_row = {
            "month_sin": np.sin(2*np.pi*m/12),
            "month_cos": np.cos(2*np.pi*m/12),
            "week_sin":  np.sin(2*np.pi*w/52),
            "week_cos":  np.cos(2*np.pi*w/52),
            "quarter":   q,
            "region_enc":    enc("region", quoted_region),
            "quality_enc":   enc("quality", quoted_quality),
            "commodity_enc": enc("commodity", "ALFALFA HAY"),
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
    except:
        pass

# ── Verdict ───────────────────────────────────────────────
# Primary diff drives title/colors — landed cost vs market+full-load freight
if landed_diff_pct > 10:
    title   = "Overpriced"
    action  = "Negotiate or Walk Away"
    bg      = "#FFF2F0"; border = "#FFD5CC"; color = "#C0392B"; pill_bg = "#C0392B"
elif landed_diff_pct > 5:
    title   = "Slightly High"
    action  = "Try to Negotiate"
    bg      = "#FFFBF0"; border = "#FFE9A0"; color = "#B07D00"; pill_bg = "#C17F3E"
elif landed_diff_pct >= -5:
    title   = "Fair Price"
    action  = "Buy Now" if forecast_dir > 8 else "Good to Go"
    bg      = "#F0FAF4"; border = "#B8E6C8"; color = "#1A7A40"; pill_bg = "#1A7A40"
else:
    title   = "Below Market"
    action  = "Buy Now"
    bg      = "#F0FAF4"; border = "#B8E6C8"; color = "#1A7A40"; pill_bg = "#1A7A40"

_ls = "above" if landed_diff >= 0 else "below"
body = (
    f"Your landed cost of <strong>${landed_per_ton:.2f}/ton</strong> is "
    f"<strong>${abs(landed_diff):.2f} ({abs(landed_diff_pct):.1f}%) {_ls}</strong> "
    f"the market estimate of <strong>${market_baseline:.2f}/ton</strong> "
    f"(regional FOB ${market_avg:.0f} + full-load freight ${full_load_freight_per_ton:.2f})."
)

freight_ctx = ""
if freight_total > 0 and quoted_price > 0:
    _fp_pct = freight_per_ton / quoted_price * 100
    freight_ctx = (
        f"<br><br>🚛 Freight (${freight_per_ton:.2f}/ton) is "
        f"<strong>{_fp_pct:.0f}%</strong> of your FOB price."
    )

no_freight_disclaimer = (
    '<br><br><span style="color:#B07D00;">⚠️ Add origin zip for '
    'freight-adjusted comparison</span>'
    if not origin_zip_clean else ""
)

vol_note = ""
if volume_tons > 0 and abs(landed_diff) * volume_tons > 50:
    _vsavings = -landed_diff * volume_tons
    if _vsavings > 0:
        vol_note = (
            f"<br><br>At {volume_tons:.2f} tons you save "
            f"<strong>${_vsavings:,.0f}</strong> vs market."
        )
    else:
        vol_note = (
            f"<br><br>At {volume_tons:.2f} tons you overpay "
            f"<strong>${abs(_vsavings):,.0f}</strong> vs market."
        )

seasonal_html = (
    f'<div style="margin-top:12px;font-size:12px;color:#8B7355;font-style:italic;">'
    f'{seasonal_note}</div>'
) if seasonal_note else ""

limited_data_html = (
    f'<div style="margin-top:10px;background:#F5F0E8;border-radius:8px;'
    f'padding:8px 12px;font-size:12px;color:#8B7355;">'
    f'⚠️ Limited recent data for this region — comparison based on '
    f'{n_trades} transactions over a wider time window. '
    f'Check back weekly as new USDA data is added.</div>'
) if "limited" in time_label.lower() else ""

if forecast_dir > 8:
    fc_bg="#FFF8F0"; fc_border="#FFD9A8"; fc_color="#A06010"
    fc_text=f"📈 Prices forecast to <strong>rise ~${forecast_dir:.0f}/ton</strong> next 7 days. If this quote is fair, consider locking it in."
elif forecast_dir < -8:
    fc_bg="#F0FAF4"; fc_border="#B8E6C8"; fc_color="#1A5C30"
    fc_text=f"📉 Prices forecast to <strong>drop ~${abs(forecast_dir):.0f}/ton</strong> next 7 days. Waiting may get you a better deal."
else:
    fc_bg="#F8F6F2"; fc_border="#E5DDD0"; fc_color="#6B6B6B"
    fc_text=f"→ Prices in {quoted_region} look stable over the next 7 days."

# ── Render verdict ────────────────────────────────────────
st.markdown(f"""
<div class="verdict-card" style="background:{bg};border:1.5px solid {border};">
  <div class="verdict-eyebrow" style="color:{color};">{title}</div>
  <div class="verdict-title" style="color:{color};">{title}</div>
  <div class="verdict-body" style="color:#3C3C3E;">{body}{freight_ctx}{no_freight_disclaimer}{vol_note}</div>
  {limited_data_html}
  {seasonal_html}
  <div class="action-pill" style="background:{pill_bg};color:#FFFFFF;">
    {action}
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="forecast-note"
     style="background:{fc_bg};border:1.5px solid {fc_border};color:{fc_color};">
  {fc_text}
</div>
""", unsafe_allow_html=True)

# ── Cost breakdown card ───────────────────────────────────
_volume_label = (
    f"{volume_tons:.2f} tons ({bale_count} bales)"
    if bale_count > 0 else f"{volume_tons:.2f} tons"
)
_freight_line = (
    f'<div style="display:flex;justify-content:space-between;font-size:14px;'
    f'margin-bottom:4px;"><span>Freight:</span>'
    f'<span><strong>${freight_total:,.2f}</strong> '
    f'<span style="color:#8B7355;font-size:12px;">(${freight_per_ton:.2f}/ton)</span>'
    f'</span></div>'
) if freight_total > 0 else ""

_unloading_line = (
    f'<div style="display:flex;justify-content:space-between;font-size:14px;'
    f'margin-bottom:4px;"><span>Unloading:</span>'
    f'<span><strong>${unloading:,.2f}</strong> '
    f'<span style="color:#8B7355;font-size:12px;">(${unloading_per_ton:.2f}/ton)</span>'
    f'</span></div>'
) if unloading > 0 else ""

_other_line = (
    f'<div style="display:flex;justify-content:space-between;font-size:14px;'
    f'margin-bottom:4px;"><span>Other fees:</span>'
    f'<span><strong>${other_fees:,.2f}</strong> '
    f'<span style="color:#8B7355;font-size:12px;">(${other_per_ton:.2f}/ton)</span>'
    f'</span></div>'
) if other_fees > 0 else ""

_per_bale_line = (
    f'<div style="font-size:14px;color:#8B7355;margin-top:2px;">'
    f'${landed_per_bale:.2f}/bale</div>'
) if bale_count > 0 else ""

st.markdown(f"""
<div style="background:#FFFFFF;border-radius:20px;padding:24px 28px;
            box-shadow:0 2px 20px rgba(0,0,0,0.06);margin-top:12px;">
  <div style="font-size:11px;font-weight:700;color:#8B7355;
              text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;">
    📦 Your Landed Cost Breakdown
  </div>
  <div style="display:flex;justify-content:space-between;font-size:13px;
              color:#8B7355;margin-bottom:12px;">
    <span>Volume:</span><span><strong style="color:#1C1C1E;">{_volume_label}</strong></span>
  </div>
  <div style="display:flex;justify-content:space-between;font-size:13px;
              color:#8B7355;margin-bottom:14px;">
    <span>FOB price:</span><span><strong style="color:#1C1C1E;">${fob_price:.2f}/ton</strong></span>
  </div>
  <div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:4px;">
    <span>Hay cost:</span><span><strong>${hay_cost:,.2f}</strong></span>
  </div>
  {_freight_line}
  {_unloading_line}
  {_other_line}
  <div style="border-top:1px solid #E5DDD0;margin:10px 0;"></div>
  <div style="display:flex;justify-content:space-between;font-size:15px;font-weight:700;">
    <span>TOTAL:</span><span>${total_cost:,.2f}</span>
  </div>
  <div style="display:flex;justify-content:space-between;font-size:18px;font-weight:800;
              color:#C17F3E;margin-top:6px;">
    <span>LANDED:</span><span>${landed_per_ton:.2f}/ton</span>
  </div>
  {_per_bale_line}
</div>
""", unsafe_allow_html=True)

# ── Partial load alert ────────────────────────────────────
if volume_tons < 35 and freight_total > 0:
    _premium_per_ton = freight_per_ton - full_load_freight_per_ton
    _premium_total   = _premium_per_ton * volume_tons
    st.markdown(f"""
<div style="background:#FFFBF0;border:1.5px solid #FFE9A0;
            border-radius:16px;padding:18px 22px;margin-top:10px;color:#B07D00;">
  <div style="font-weight:800;font-size:15px;margin-bottom:8px;">
    ⚠️ Partial Load Premium
  </div>
  <div style="font-size:14px;line-height:1.7;">
    Your freight: <strong>${freight_per_ton:.2f}/ton</strong><br>
    Full load:    <strong>${full_load_freight_per_ton:.2f}/ton</strong> (at 40 tons)<br>
    Premium:      <strong>${_premium_per_ton:.2f}/ton extra</strong>
  </div>
  <div style="font-size:13px;margin-top:10px;color:#A06010;">
    Filling the truck saves ${_premium_per_ton:.2f}/ton →
    <strong>${_premium_total:,.0f}</strong> on {volume_tons:.2f} tons.
  </div>
</div>
""", unsafe_allow_html=True)

# ── Market comparison detail ──────────────────────────────
_mc_color = "#1A7A40" if landed_diff <= 0 else ("#B07D00" if landed_diff_pct <= 10 else "#C0392B")
_mc_arrow = "✅ BELOW MARKET" if landed_diff <= 0 else (
    "⚠️ ABOVE MARKET" if landed_diff_pct <= 10 else "❌ OVERPRICED"
)
_mc_total = landed_diff * volume_tons
_mc_total_label = (
    f"Total {'overpay' if _mc_total > 0 else 'savings'}: "
    f"<strong>${abs(_mc_total):,.2f}</strong>"
) if abs(_mc_total) > 1 else ""

st.markdown(f"""
<div style="background:#FFFFFF;border-radius:16px;padding:18px 22px;
            box-shadow:0 2px 12px rgba(0,0,0,0.05);margin-top:10px;
            border-left:4px solid {_mc_color};">
  <div style="font-size:11px;font-weight:700;color:#8B7355;
              text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">
    Landed cost vs market
  </div>
  <div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:4px;">
    <span>Your landed cost:</span><span><strong>${landed_per_ton:.2f}/ton</strong></span>
  </div>
  <div style="display:flex;justify-content:space-between;font-size:14px;margin-bottom:4px;">
    <span>Market estimate:</span><span><strong>${market_baseline:.2f}/ton</strong></span>
  </div>
  <div style="display:flex;justify-content:space-between;font-size:14px;
              color:{_mc_color};font-weight:700;margin-top:6px;">
    <span>Difference:</span>
    <span>${landed_diff:+.2f}/ton  {_mc_arrow}</span>
  </div>
  <div style="font-size:12px;color:#8B7355;margin-top:6px;">{_mc_total_label}</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="stat-row">
  <div class="stat-card">
    <div class="stat-label">Market Low</div>
    <div class="stat-value" style="color:#1A7A40;">${market_lo:.0f}</div>
    <div class="stat-sub">per ton</div>
  </div>
  <div class="stat-card" style="border:1.5px solid {border};">
    <div class="stat-label">Your Quote</div>
    <div class="stat-value" style="color:{color};">${quoted_price}</div>
    <div class="stat-sub" style="color:{color};">{pct_rank:.0f}th percentile</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Market High</div>
    <div class="stat-value" style="color:#C0392B;">${market_hi:.0f}</div>
    <div class="stat-sub">per ton</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="position-card">
  <div class="position-label">
    <span>Price Position</span>
    <span style="color:{color};">{pct_rank:.0f}th percentile</span>
  </div>
  <div class="bar-track">
    <div class="bar-fill"
         style="width:{pct_rank:.0f}%;
                background:linear-gradient(90deg,#52C77A,{color});">
      <div class="bar-dot" style="background:{color};"></div>
    </div>
  </div>
  <div class="bar-ends">
    <span>Best deal · ${market_lo:.0f}</span>
    <span>${market_hi:.0f} · Most expensive</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Chart ─────────────────────────────────────────────────
region_history = df_prices[
    (df_prices["state"]  == "California") &
    (df_prices["region"] == quoted_region) &
    (df_prices["date"]   >= (df_prices["date"].max() - pd.Timedelta(days=180)))
].groupby("date")["price_avg"].mean().reset_index()

if len(region_history) > 3:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=region_history["date"],
        y=region_history["price_avg"],
        mode="lines",
        line=dict(color="#C17F3E", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(193,127,62,0.07)",
        hovertemplate="$%{y:.0f}/ton<br>%{x|%b %d}<extra>Market avg</extra>",
    ))
    fig.add_hline(
        y=quoted_price,
        line_dash="solid", line_color=color, line_width=2,
        annotation_text=f"  Your quote ${quoted_price}",
        annotation_font=dict(size=12, color=color),
        annotation_position="top left",
    )
    fig.add_hline(
        y=market_avg,
        line_dash="dot", line_color="#AEAEB2", line_width=1.5,
        annotation_text=f"  Avg ${market_avg:.0f}",
        annotation_font=dict(size=11, color="#AEAEB2"),
        annotation_position="bottom right",
    )
    fig.update_layout(
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        font=dict(family="Nunito Sans", color="#6B6B6B", size=11),
        margin=dict(t=20, b=20, l=10, r=10),
        height=190, showlegend=False, hovermode="x unified",
        xaxis=dict(gridcolor="#F2EDE4", showgrid=False),
        yaxis=dict(gridcolor="#F2EDE4"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Freight display ────────────────────────────────────────
if _freight_data:
    _d  = _freight_data["dist"]
    _f  = _freight_data["freight"]
    _dp = _freight_data["diesel"]
    _all_in        = quoted_price + _f["freight_per_ton"]
    _surcharge_note = (
        f"${_f['fuel_surcharge']:.2f} fuel surcharge"
        if _f["fuel_surcharge"] > 0 else "No fuel surcharge"
    )
    st.markdown(f"""
<div style="background:#FFFFFF;border-radius:20px;padding:24px 28px;
            box-shadow:0 2px 20px rgba(0,0,0,0.06);margin-top:12px;">
  <div style="font-size:11px;font-weight:700;color:#8B7355;
              text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;">
    🚛 Freight Estimate
  </div>
  <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px;">
    <div style="flex:1;min-width:110px;background:#F5F0E8;border-radius:12px;
                padding:12px 14px;text-align:center;">
      <div style="font-size:11px;color:#8B7355;text-transform:uppercase;
                  font-weight:700;letter-spacing:0.08em;">Distance</div>
      <div style="font-size:22px;font-weight:800;color:#1C1C1E;margin-top:4px;">
        {_d['miles']:.1f}
      </div>
      <div style="font-size:11px;color:#8B7355;">miles</div>
    </div>
    <div style="flex:1;min-width:110px;background:#F5F0E8;border-radius:12px;
                padding:12px 14px;text-align:center;">
      <div style="font-size:11px;color:#8B7355;text-transform:uppercase;
                  font-weight:700;letter-spacing:0.08em;">Freight Total</div>
      <div style="font-size:22px;font-weight:800;color:#C17F3E;margin-top:4px;">
        ${_f['total_freight']:,.0f}
      </div>
      <div style="font-size:11px;color:#8B7355;">per load</div>
    </div>
    <div style="flex:1;min-width:110px;background:#F5F0E8;border-radius:12px;
                padding:12px 14px;text-align:center;">
      <div style="font-size:11px;color:#8B7355;text-transform:uppercase;
                  font-weight:700;letter-spacing:0.08em;">Freight / Ton</div>
      <div style="font-size:22px;font-weight:800;color:#C17F3E;margin-top:4px;">
        ${_f['freight_per_ton']:.2f}
      </div>
      <div style="font-size:11px;color:#8B7355;">per ton</div>
    </div>
    <div style="flex:1;min-width:110px;background:#1C1C1E;border-radius:12px;
                padding:12px 14px;text-align:center;">
      <div style="font-size:11px;color:#AEAEB2;text-transform:uppercase;
                  font-weight:700;letter-spacing:0.08em;">All-In Cost</div>
      <div style="font-size:22px;font-weight:800;color:#FFFFFF;margin-top:4px;">
        ${_all_in:.2f}
      </div>
      <div style="font-size:11px;color:#AEAEB2;">per ton delivered</div>
    </div>
  </div>
  <div style="font-size:12px;color:#8B7355;line-height:1.6;border-top:1px solid #E5DDD0;
              padding-top:10px;">
    📍 {_d['origin_address']} → {_d['destination_address']}<br>
    $5.00/mi · ${_f['base_total']:,.0f} base · {_surcharge_note}
    (diesel ${_dp:.3f}/gal)
  </div>
</div>
""", unsafe_allow_html=True)
elif _freight_error:
    st.warning(f"Freight estimate unavailable: {_freight_error}")

# ── Regional sourcing intelligence ────────────────────────
if check and quoted_region:
    _gmaps_key_s = st.secrets.get("GOOGLE_MAPS_API_KEY", "")
    _diesel_s    = _freight_data["diesel"] if _freight_data else get_current_diesel()
    _vol_s       = max(quoted_volume, 1)
    with st.spinner("Finding better sources…"):
        _sources = find_cheaper_sources(
            zip_clean, quoted_price, quoted_quality,
            is_alfalfa_input, df_prices, _diesel_s,
            _gmaps_key_s, _zip_map, _vol_s,
        )
    if _sources:
        st.markdown("""
<div style="font-size:11px;font-weight:700;color:#8B7355;text-transform:uppercase;
            letter-spacing:0.1em;margin:20px 0 10px;">
  📦 Cheaper Sources Found
</div>
""", unsafe_allow_html=True)
        for i, src in enumerate(_sources):
            _medal   = ["🥇", "🥈", "🥉"][i]
            _savings = src["savings_per_ton"]
            _total_s = _savings * _vol_s if quoted_volume > 0 else None
            _total_html = (
                f'<span style="font-size:12px;color:#1A7A40;">'
                f'Save ${_total_s:,.0f} total on {quoted_volume} tons</span>'
            ) if _total_s and _total_s > 50 else ""
            st.markdown(f"""
<div style="background:#FFFFFF;border-radius:16px;padding:18px 22px;
            box-shadow:0 2px 12px rgba(0,0,0,0.05);margin-bottom:10px;
            border-left:4px solid #1A7A40;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;
              flex-wrap:wrap;gap:8px;">
    <div>
      <div style="font-size:16px;font-weight:800;color:#1C1C1E;">
        {_medal} {src['region']}
      </div>
      <div style="font-size:12px;color:#8B7355;margin-top:2px;">
        {src['miles']:.0f} mi · {src['count']} trades in last 13 weeks
      </div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:22px;font-weight:800;color:#1A7A40;">
        ${src['delivered_est']:.0f}/ton delivered
      </div>
      <div style="font-size:13px;font-weight:700;color:#1A7A40;">
        Save ${_savings:.2f}/ton vs your quote
      </div>
      {_total_html}
    </div>
  </div>
  <div style="display:flex;gap:16px;margin-top:12px;flex-wrap:wrap;">
    <div style="font-size:12px;color:#6B6B6B;">
      FOB avg <strong style="color:#1C1C1E;">${src['avg_fob']:.0f}</strong>
    </div>
    <div style="font-size:12px;color:#6B6B6B;">
      + freight <strong style="color:#1C1C1E;">${src['freight_per_ton']:.2f}</strong>/ton
    </div>
    <div style="font-size:12px;color:#6B6B6B;">
      = delivered <strong style="color:#1A7A40;">${src['delivered_est']:.0f}</strong>/ton
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────
st.markdown(f"""
<div class="data-footer">
  {data_label} · {time_label} · {n_trades} transactions · USDA AMS<br>
  Forecast: XGBoost · MAE ±$17.59/ton · Updated daily<br>
  Market intelligence only — not financial advice
</div>
""", unsafe_allow_html=True)
