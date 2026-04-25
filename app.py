import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import joblib
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

col1, col2 = st.columns(2)
with col1:
    quoted_price = st.number_input(
        "Price quoted $/ton",
        min_value=50, max_value=800,
        value=180, step=5,
    )
with col2:
    zip_input = st.text_input(
        "Your zip code",
        placeholder="e.g. 93706",
        max_chars=5,
    )

# Zip → region
import json as _json
_zip_map = {}
if os.path.exists("zip_to_region.json"):
    with open("zip_to_region.json") as _zf:
        _zip_map = _json.load(_zf)

zip_clean          = zip_input.strip() if zip_input else ""
auto_region        = _zip_map.get(zip_clean, None)
quoted_region      = None
zip_not_in_service = False

if zip_clean and len(zip_clean) == 5 and zip_clean.isdigit():
    if auto_region:
        quoted_region = auto_region
        st.markdown(f"""
        <div style="background:#F0FAF4;border:1.5px solid #B8E6C8;
                    border-radius:10px;padding:10px 14px;
                    margin-top:-8px;margin-bottom:8px;
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
                margin-top:-8px;font-size:13px;color:#B07D00;">
      Keep typing...
    </div>
    """, unsafe_allow_html=True)

col3, col4 = st.columns(2)
with col3:
    quoted_quality = st.selectbox(
        "Quality grade",
        options=QUALITIES, index=1,
    )
with col4:
    quoted_volume = st.number_input(
        "Volume (tons) optional",
        min_value=0, max_value=10000,
        value=0, step=10,
    )

col5, col6 = st.columns(2)
with col5:
    is_alfalfa_input = st.checkbox("🌿  Pure Alfalfa", value=True)
with col6:
    is_delivered_input = st.checkbox("🚛  Delivered price", value=True)

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
MIN_RECORDS = 5

def get_base_data(df, region, weeks_back):
    cutoff = df["date"].max() - pd.Timedelta(weeks=weeks_back)
    data   = df[
        (df["state"]  == "California") &
        (df["region"] == region) &
        (df["date"]   >= cutoff)
    ].copy()
    if is_alfalfa_input and "is_alfalfa" in data.columns:
        sub = data[data["is_alfalfa"] == 1]
        if len(sub) >= MIN_RECORDS: data = sub
    if is_delivered_input and "is_delivered" in data.columns:
        sub = data[data["is_delivered"] == 1]
        if len(sub) >= MIN_RECORDS: data = sub
    return data

def get_quality_data(base, quality):
    return base[base["quality"].str.contains(quality, case=False, na=False)]

def calc_stats(data):
    return (
        data["price_avg"].mean(),
        data["price_avg"].min(),
        data["price_avg"].max(),
        len(data),
    )

market_avg = market_lo = market_hi = None
n_trades   = 0
data_label = ""
time_label = ""

if quoted_region:
    for weeks, label in [(4,"last 4 weeks"),(8,"last 8 weeks"),(13,"last 13 weeks")]:
        base  = get_base_data(df_prices, quoted_region, weeks)
        qdata = get_quality_data(base, quoted_quality)
        if len(qdata) >= MIN_RECORDS:
            market_avg, market_lo, market_hi, n_trades = calc_stats(qdata)
            data_label = f"{quoted_quality} · {quoted_region}"
            time_label = label
            break

    if market_avg is None:
        base = get_base_data(df_prices, quoted_region, 4)
        if len(base) >= MIN_RECORDS:
            market_avg, market_lo, market_hi, n_trades = calc_stats(base)
            data_label = f"{quoted_region} (all grades)"
            time_label = "last 4 weeks"

    if market_avg is None:
        cutoff  = df_prices["date"].max() - pd.Timedelta(weeks=13)
        ca_data = df_prices[
            (df_prices["state"] == "California") &
            (df_prices["date"]  >= cutoff)
        ]
        qdata = get_quality_data(ca_data, quoted_quality)
        if len(qdata) >= MIN_RECORDS:
            market_avg, market_lo, market_hi, n_trades = calc_stats(qdata)
            data_label = f"{quoted_quality} · CA Statewide"
            time_label = "last 13 weeks"
        elif len(ca_data) >= MIN_RECORDS:
            market_avg, market_lo, market_hi, n_trades = calc_stats(ca_data)
            data_label = "CA Statewide"
            time_label = "last 13 weeks"

if market_avg is None:
    st.warning("Not enough market data for this region yet.")
    st.stop()

market_avg = round(market_avg, 1)
market_lo  = round(market_lo,  1)
market_hi  = round(market_hi,  1)
diff       = quoted_price - market_avg
diff_pct   = diff / market_avg * 100
pct_rank   = max(0, min(100,
    (quoted_price - market_lo) / (market_hi - market_lo) * 100
    if market_hi > market_lo else 50
))

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
if diff_pct > 10:
    title   = "Overpriced"
    action  = "Negotiate or Walk Away"
    body    = f"You were quoted <strong>${quoted_price}/ton</strong> — that's <strong>${diff:.0f} ({diff_pct:.1f}%) above</strong> the {data_label} average of <strong>${market_avg:.0f}/ton</strong> ({time_label}). Push back hard or find another seller."
    bg      = "#FFF2F0"; border = "#FFD5CC"; color = "#C0392B"; pill_bg = "#C0392B"
elif diff_pct > 5:
    title   = "Slightly High"
    action  = "Try to Negotiate"
    body    = f"You were quoted <strong>${quoted_price}/ton</strong> — <strong>${diff:.0f} ({diff_pct:.1f}%) above</strong> the {data_label} average of <strong>${market_avg:.0f}/ton</strong> ({time_label}). You have room to push back."
    bg      = "#FFFBF0"; border = "#FFE9A0"; color = "#B07D00"; pill_bg = "#C17F3E"
elif diff_pct >= -5:
    title   = "Fair Price"
    action  = "Buy Now" if forecast_dir > 8 else "Good to Go"
    body    = f"You were quoted <strong>${quoted_price}/ton</strong> — within <strong>${abs(diff):.0f} ({abs(diff_pct):.1f}%)</strong> of the {data_label} average of <strong>${market_avg:.0f}/ton</strong> ({time_label}). This is a fair deal."
    bg      = "#F0FAF4"; border = "#B8E6C8"; color = "#1A7A40"; pill_bg = "#1A7A40"
else:
    title   = "Below Market"
    action  = "Buy Now"
    body    = f"You were quoted <strong>${quoted_price}/ton</strong> — <strong>${abs(diff):.0f} ({abs(diff_pct):.1f}%) below</strong> the {data_label} average of <strong>${market_avg:.0f}/ton</strong> ({time_label}). This is a great deal — act fast."
    bg      = "#F0FAF4"; border = "#B8E6C8"; color = "#1A7A40"; pill_bg = "#1A7A40"

vol_note = ""
if quoted_volume > 0:
    overpay = diff * quoted_volume
    if abs(overpay) > 50:
        if overpay > 0:
            vol_note = f"<br><br>At {quoted_volume} tons, you'd <strong>overpay ${overpay:,.0f}</strong> vs market."
        else:
            vol_note = f"<br><br>At {quoted_volume} tons, you'd <strong>save ${abs(overpay):,.0f}</strong> vs market."

if forecast_dir > 8:
    fc_bg="#FFF8F0"; fc_border="#FFD9A8"; fc_color="#A06010"
    fc_text=f"📈 Prices forecast to <strong>rise ~${forecast_dir:.0f}/ton</strong> next 7 days. If this quote is fair, consider locking it in."
elif forecast_dir < -8:
    fc_bg="#F0FAF4"; fc_border="#B8E6C8"; fc_color="#1A5C30"
    fc_text=f"📉 Prices forecast to <strong>drop ~${abs(forecast_dir):.0f}/ton</strong> next 7 days. Waiting may get you a better deal."
else:
    fc_bg="#F8F6F2"; fc_border="#E5DDD0"; fc_color="#6B6B6B"
    fc_text=f"→ Prices in {quoted_region} look stable over the next 7 days."

# ── Render ────────────────────────────────────────────────
st.markdown(f"""
<div class="verdict-card" style="background:{bg};border:1.5px solid {border};">
  <div class="verdict-eyebrow" style="color:{color};">{title}</div>
  <div class="verdict-title" style="color:{color};">{title}</div>
  <div class="verdict-body" style="color:#3C3C3E;">{body}{vol_note}</div>
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

# ── Admin ─────────────────────────────────────────────────
if st.session_state.user_email.lower() == "salvador.guzman224@gmail.com":
    with st.expander("📍 Admin — Unserved Zip Codes"):
        if os.path.exists("unserved_zips.json"):
            with open("unserved_zips.json") as f:
                unserved = json.load(f)
            if unserved:
                df_zips = pd.DataFrame([
                    {"zip": z, "attempts": c}
                    for z,c in sorted(unserved.items(),
                                      key=lambda x: x[1], reverse=True)
                ])
                st.dataframe(df_zips, use_container_width=True, hide_index=True)
                st.download_button("Download CSV",
                    df_zips.to_csv(index=False),
                    "unserved_zips.csv", "text/csv")
            else:
                st.write("No unserved zips yet")

    with st.expander("👤 Admin — User Signups"):
        users = load_users()
        if users:
            df_users = pd.DataFrame([
                {
                    "email":     email,
                    "name":      u.get("name",""),
                    "operation": u.get("operation_type",""),
                    "state":     u.get("state",""),
                    "checks":    u.get("checks",0),
                    "joined":    u.get("joined","")[:10],
                }
                for email, u in users.items()
            ])
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            st.download_button("Download user list",
                df_users.to_csv(index=False),
                "hayscout_users.csv", "text/csv")
        else:
            st.write("No signups yet")

# ── Footer ────────────────────────────────────────────────
st.markdown(f"""
<div class="data-footer">
  {data_label} · {time_label} · {n_trades} transactions · USDA AMS<br>
  Forecast: XGBoost · MAE ±$17.59/ton · Updated daily<br>
  Market intelligence only — not financial advice
</div>
""", unsafe_allow_html=True)
