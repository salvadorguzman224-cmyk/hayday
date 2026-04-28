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
    "hoyt_prices_clean.csv":                    "1kpOqZAEDn_Ha_xKkePdwlhuuqyVUfH23",
}

for local_path, file_id in DRIVE_FILES.items():
    _gdrive_download(file_id, local_path)

# ── Imports ───────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime, date

# ── Supabase config ───────────────────────────────────────────────────────
SUPABASE_URL = "https://xffnfprrnwjnvnokbojd.supabase.co"
SUPABASE_KEY = "sb_publishable_co30W4DCMSOI7qNyumEhiQ_IQZjzu2W"

def _sb_insert(table, row):
    """Insert a row into a Supabase table."""
    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json=row,
            timeout=10,
        )
        return r.status_code in [200, 201]
    except Exception:
        return False

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
.stApp { background: #F5F0E8; color: #1C1C1E; }
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 48px 20px 80px !important;
    max-width: 640px !important;
    margin: 0 auto;
}

/* Logo */
.hayday-logo {
    text-align: center;
    margin-bottom: 4px;
}
.hayday-logo-text {
    font-family: "Nunito", sans-serif;
    font-size: 40px;
    font-weight: 800;
    color: #1C1C1E;
    letter-spacing: -1px;
}
.hayday-logo-ai { color: #C17F3E; }
.hayday-tagline {
    text-align: center;
    font-size: 15px;
    color: #8B7355;
    margin-bottom: 32px;
}

/* Card */
.card {
    background: #FFFFFF;
    border-radius: 20px;
    padding: 28px 24px;
    box-shadow: 0 2px 20px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}

/* Toggle chips for buyer/seller */
.role-row {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
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
    margin-top: 8px;
}
.stButton > button:hover { background: #A86D32 !important; }

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
}

/* Verdict cards */
.verdict-buy {
    background: #F0FAF4;
    border: 2px solid #1A7A40;
    border-radius: 20px;
    padding: 28px 24px;
    text-align: center;
    margin-bottom: 16px;
}
.verdict-negotiate {
    background: #FFFBF0;
    border: 2px solid #C17F3E;
    border-radius: 20px;
    padding: 28px 24px;
    text-align: center;
    margin-bottom: 16px;
}
.verdict-wait {
    background: #FFF5F5;
    border: 2px solid #C0392B;
    border-radius: 20px;
    padding: 28px 24px;
    text-align: center;
    margin-bottom: 16px;
}
.verdict-icon { font-size: 52px; margin-bottom: 8px; }
.verdict-label {
    font-family: "Nunito", sans-serif;
    font-size: 32px;
    font-weight: 800;
    margin-bottom: 6px;
}
.verdict-label-buy     { color: #1A7A40; }
.verdict-label-neg     { color: #C17F3E; }
.verdict-label-wait    { color: #C0392B; }
.verdict-sub { font-size: 15px; color: #555; line-height: 1.5; }

/* Benchmark table */
.bench-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 20px 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    margin-bottom: 16px;
}
.bench-title {
    font-size: 12px;
    font-weight: 700;
    color: #8B7355;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 14px;
}
.bench-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #F0EAE0;
}
.bench-row:last-child { border-bottom: none; }
.bench-source { font-size: 13px; color: #555; }
.bench-source-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 8px;
}
.bench-price {
    font-size: 15px;
    font-weight: 700;
    color: #1C1C1E;
}
.bench-gap-above { font-size: 12px; color: #C0392B; }
.bench-gap-below { font-size: 12px; color: #1A7A40; }
.bench-gap-even  { font-size: 12px; color: #8B7355; }

/* Tip box */
.tip-box {
    background: #F5F0E8;
    border-radius: 12px;
    padding: 14px 16px;
    font-size: 13px;
    color: #5C4A2A;
    line-height: 1.6;
    margin-bottom: 16px;
}
.tip-box strong { color: #C17F3E; }

/* Stat chips */
.stat-row {
    display: flex;
    gap: 10px;
    margin-bottom: 16px;
}
.stat-chip {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 12px 10px;
    flex: 1;
    text-align: center;
    box-shadow: 0 1px 8px rgba(0,0,0,0.04);
}
.stat-icon { font-size: 18px; }
.stat-label { font-size: 10px; color: #8B7355; margin-top: 2px; }
.stat-value { font-size: 13px; font-weight: 700; color: #1C1C1E; margin-top: 2px; }

/* Disclaimer */
.disclaimer {
    text-align: center;
    font-size: 11px;
    color: #B0A090;
    margin-top: 8px;
}
.powered-by {
    text-align: center;
    font-size: 11px;
    color: #B0A090;
    margin-top: 16px;
    padding-bottom: 20px;
}

/* Widget labels */
.stTextInput label, .stSelectbox label, .stNumberInput label, .stRadio label {
    font-family: "Nunito Sans", sans-serif !important;
    font-size: 13px !important;
    color: #8B7355 !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Load reference data ───────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_reference_data():
    prices = pd.read_csv("ca_hay_prices_v2_clean.csv", parse_dates=["date"])
    diesel = pd.read_csv("diesel_prices.csv", parse_dates=["date"])
    milk   = pd.read_csv("milk_price_ca_clean.csv")
    cattle = pd.read_csv("cattle_monthly_cap.csv")
    stocks = pd.read_csv("hay_stocks_features.csv")
    water  = pd.read_csv("water_allocation.csv")
    nass   = pd.read_csv("nass_supply_data.csv")

    # Hoyt data
    hoyt = None
    if os.path.exists("hoyt_prices_clean.csv"):
        hoyt = pd.read_csv("hoyt_prices_clean.csv", parse_dates=["report_date"])

    return prices, diesel, milk, cattle, stocks, water, nass, hoyt

@st.cache_resource
def load_model():
    try:
        bundle = joblib.load("models/xgboost_v12f_20260427_235122.pkl")
        return bundle
    except Exception as e:
        return None

# ── Benchmark helpers ─────────────────────────────────────────────────────
def get_usda_benchmark(prices, region, grade):
    """Most recent USDA AMS price for this region + grade."""
    CA_GRADES = {
        "Supreme": ["Supreme", "Premium/Supreme"],
        "Premium": ["Premium", "Good/Premium", "Premium/Supreme"],
        "Good":    ["Good", "Fair/Good", "Good/Premium"],
        "Fair":    ["Fair", "Fair/Good", "Utility/Fair"],
    }
    grade_variants = CA_GRADES.get(grade, [grade])
    subset = prices[
        (prices["region"] == region) &
        (prices["quality"].isin(grade_variants))
    ].sort_values("date")
    if subset.empty:
        return None, None
    recent = subset.tail(8)
    return round(float(recent["price_avg"].mean()), 2), str(subset["date"].iloc[-1].date())

def get_hoyt_benchmark(hoyt, region, grade):
    """Most recent Hoyt price for this region + grade."""
    if hoyt is None or hoyt.empty:
        return None, None
    # Map region names
    HOYT_REGION_MAP = {
        "Central San Joaquin Valley": "Central San Joaquin Valley",
        "North San Joaquin Valley":   "North San Joaquin Valley",
        "Sacramento Valley":          "Sacramento Valley",
        "North Inter-Mountains":      "North Inter-Mountains",
        "Southeast":                  "Southeast",
    }
    hoyt_region = HOYT_REGION_MAP.get(region)
    if not hoyt_region:
        return None, None
    subset = hoyt[
        (hoyt["region_name"] == hoyt_region) &
        (hoyt["grade"].str.contains(grade, case=False, na=False)) &
        (hoyt["time_ref"] == "most_recent")
    ].sort_values("report_date")
    if subset.empty:
        return None, None
    recent = subset.tail(4)
    return round(float(recent["price_avg"].mean()), 2), str(subset["report_date"].iloc[-1].date())

def get_model_prediction(bundle, region, grade, prices, diesel, milk, cattle, stocks, water, nass):
    """Run v12f model prediction."""
    try:
        model    = bundle["model"]
        features = bundle["features"]
        encoders = bundle["encoders"]

        now   = datetime.now()
        year  = now.year
        month = now.month
        week  = int(now.isocalendar()[1])

        month_sin = np.sin(2 * np.pi * month / 12)
        month_cos = np.cos(2 * np.pi * month / 12)
        week_sin  = np.sin(2 * np.pi * week / 52)
        week_cos  = np.cos(2 * np.pi * week / 52)
        quarter   = (month - 1) // 3 + 1

        def safe_enc(enc, val, fallback=0):
            try: return int(enc.transform([val])[0])
            except: return fallback

        region_enc    = safe_enc(encoders["region"],    region)
        quality_enc   = safe_enc(encoders["quality"],   grade)
        commodity_enc = safe_enc(encoders["commodity"], "Hay")

        recent = prices[
            (prices["region"] == region) &
            (prices["quality"].str.contains(grade, case=False, na=False))
        ].sort_values("date").tail(20)

        fallback = float(prices[prices["region"] == region]["price_avg"].median())
        lag_4w       = float(recent["price_avg"].iloc[-4])  if len(recent) >= 4  else fallback
        lag_13w      = float(recent["price_avg"].iloc[-13]) if len(recent) >= 13 else fallback
        roll_4w_mean = float(recent["price_avg"].tail(4).mean()) if len(recent) >= 1 else fallback

        d = diesel.sort_values("date")
        diesel_4w_avg  = float(d.tail(4)["diesel_price"].mean())
        diesel_13w_avg = float(d.tail(13)["diesel_price"].mean())

        milk["month"] = milk["month"].astype(int)
        mk = milk[(milk["year"]==year)&(milk["month"]==month)]
        if mk.empty: mk = milk.sort_values(["year","month"]).tail(1)
        milk_price_cwt = float(mk["milk_price_cwt"].values[0])

        cattle["month"] = cattle["month"].astype(int)
        ct = cattle[(cattle["year"]==year)&(cattle["month"]==month)]
        if ct.empty: ct = cattle.sort_values(["year","month"]).tail(1)
        cattle_on_feed_ca = float(ct["cattle_on_feed_ca"].values[0])

        def latest(df, yr):
            r = df[df["year"]==yr]
            return r if not r.empty else df.sort_values("year").tail(1)

        sr = latest(stocks, year)
        wr = latest(water,  year)
        nr = latest(nass,   year)

        row = {
            "month_sin": month_sin, "month_cos": month_cos,
            "week_sin": week_sin, "week_cos": week_cos, "quarter": quarter,
            "region_enc": region_enc, "quality_enc": quality_enc,
            "commodity_enc": commodity_enc,
            "lag_4w": lag_4w, "lag_13w": lag_13w, "roll_4w_mean": roll_4w_mean,
            "diesel_4w_avg": diesel_4w_avg, "diesel_13w_avg": diesel_13w_avg,
            "milk_price_cwt": milk_price_cwt,
            "cattle_on_feed_ca": cattle_on_feed_ca,
            "stocks_may":     float(sr["stocks_may"].values[0]),
            "stocks_may_yoy": float(sr["stocks_may_yoy"].values[0]),
            "avg_allocation": float(wr["avg_allocation"].values[0]),
            "drought_year":   float(wr["drought_year"].values[0]),
            "production_tons":    float(nr["production_tons"].values[0]),
            "acres_harvested":    float(nr["acres_harvested"].values[0]),
            "yield_tons_per_acre":float(nr["yield_tons_per_acre"].values[0]),
            "alfalfa_share":      float(nr["alfalfa_share"].values[0]),
            "is_alfalfa":      1 if grade in ["Supreme","Premium"] else 0,
            "is_delivered":    1,
            "is_dairy_buyer":  1,
            "is_large_square": 1,
            "has_quality_issue": 0,
        }

        X = pd.DataFrame([row])[features].astype(float)
        return round(float(model.predict(X)[0]), 2)
    except Exception as e:
        return None

def get_market_price(model_pred, usda_price, hoyt_price):
    """Weighted consensus market price from available sources."""
    prices, weights = [], []
    if model_pred:
        prices.append(model_pred); weights.append(0.5)
    if usda_price:
        prices.append(usda_price); weights.append(0.35)
    if hoyt_price:
        prices.append(hoyt_price); weights.append(0.15)
    if not prices:
        return None
    total_w = sum(weights)
    return round(sum(p*w for p,w in zip(prices,weights)) / total_w, 2)

def get_verdict(user_price, market_price, user_type):
    """Return verdict + messaging for buyer or seller."""
    gap     = user_price - market_price
    gap_pct = (gap / market_price) * 100

    THRESHOLD = 5.0  # % within which = negotiate

    if user_type == "Buyer":
        if gap_pct < -THRESHOLD:
            return "buy", gap, gap_pct
        elif gap_pct <= THRESHOLD:
            return "negotiate", gap, gap_pct
        else:
            return "wait", gap, gap_pct
    else:  # Seller
        if gap_pct > THRESHOLD:
            return "buy", gap, gap_pct   # "sell" uses same green card
        elif gap_pct >= -THRESHOLD:
            return "negotiate", gap, gap_pct
        else:
            return "wait", gap, gap_pct

VERDICT_CONTENT = {
    "Buyer": {
        "buy": {
            "icon": "✅",
            "label": "Buy It",
            "label_cls": "verdict-label-buy",
            "card_cls": "verdict-buy",
            "sub": "This price is below market. Lock it in before it moves.",
            "tip": "<strong>Negotiation tip:</strong> You're already in good shape — but you can still ask for better freight terms or volume discounts if buying in bulk.",
        },
        "negotiate": {
            "icon": "🤝",
            "label": "Negotiate",
            "label_cls": "verdict-label-neg",
            "card_cls": "verdict-negotiate",
            "sub": "This price is near market. There's room to push.",
            "tip": "<strong>Negotiation tip:</strong> Reference USDA AMS market data. Ask for a 3–5% reduction or request delivered pricing instead of FOB.",
        },
        "wait": {
            "icon": "⏳",
            "label": "Wait",
            "label_cls": "verdict-label-wait",
            "card_cls": "verdict-wait",
            "sub": "This price is above market. You can do better.",
            "tip": "<strong>Negotiation tip:</strong> Tell the seller you've seen market data putting prices lower. Ask them to match or walk away and check other suppliers.",
        },
    },
    "Seller": {
        "buy": {
            "icon": "✅",
            "label": "Sell It",
            "label_cls": "verdict-label-buy",
            "card_cls": "verdict-buy",
            "sub": "This offer is above market. Accept it.",
            "tip": "<strong>Tip:</strong> Strong offer — close it now. If the buyer is motivated, you might push 2–3% higher, but don't risk losing it.",
        },
        "negotiate": {
            "icon": "🤝",
            "label": "Negotiate",
            "label_cls": "verdict-label-neg",
            "card_cls": "verdict-negotiate",
            "sub": "Fair offer, but market supports a higher price.",
            "tip": "<strong>Tip:</strong> Counter 5% higher. Reference recent USDA AMS prices in your region. Buyers expect some back-and-forth.",
        },
        "wait": {
            "icon": "⏳",
            "label": "Hold",
            "label_cls": "verdict-label-wait",
            "card_cls": "verdict-wait",
            "sub": "This offer is below market. You can get more.",
            "tip": "<strong>Tip:</strong> Don't take it. Share USDA market data with the buyer. If storage allows, wait — prices in your region support better offers.",
        },
    },
}

# ── Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hayday-logo">
  <span class="hayday-logo-text">HayDay<span class="hayday-logo-ai">.ai</span></span>
</div>
<p class="hayday-tagline">Is it a good deal? Find out in seconds.</p>
""", unsafe_allow_html=True)

# ── Input card ────────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)

user_type = st.radio(
    "I am a",
    ["Buyer", "Seller"],
    horizontal=True,
)

REGION_OPTIONS = [
    "Southeast",
    "North San Joaquin Valley",
    "Sacramento Valley",
    "North Inter-Mountains",
    "Central San Joaquin Valley",
]
region = st.selectbox("Region", REGION_OPTIONS)
grade  = st.selectbox("Hay Grade", ["Supreme", "Premium", "Good", "Fair"])

price_label = "Price you were quoted ($/ton)" if user_type == "Buyer" else "Price you were offered ($/ton)"
user_price  = st.number_input(price_label, min_value=50.0, max_value=800.0,
                               value=200.0, step=5.0)

check_btn = st.button("Check My Deal →")
st.markdown('</div>', unsafe_allow_html=True)

# ── Analysis ──────────────────────────────────────────────────────────────
if check_btn:

    # Loading animation
    loading = st.empty()
    loading.markdown("""
    <div class="loading-wrap">
      <div class="loading-bale">🌾</div>
      <p class="loading-text">Checking California hay market data…</p>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(5)
    loading.empty()

    try:
        prices, diesel, milk, cattle, stocks, water, nass, hoyt = load_reference_data()
        bundle = load_model()

        # Get benchmarks
        usda_price, usda_date   = get_usda_benchmark(prices, region, grade)
        hoyt_price, hoyt_date   = get_hoyt_benchmark(hoyt, region, grade)
        model_pred               = get_model_prediction(
            bundle, region, grade, prices, diesel, milk, cattle, stocks, water, nass
        ) if bundle else None

        # Consensus market price
        market_price = get_market_price(model_pred, usda_price, hoyt_price)

        if market_price is None:
            st.error("Not enough market data for this region and grade. Try a different combination.")
            st.stop()

        # Verdict
        verdict, gap, gap_pct = get_verdict(user_price, market_price, user_type)
        content = VERDICT_CONTENT[user_type][verdict]

        # Gap display
        gap_str    = f"${abs(gap):.0f}/ton {'below' if gap < 0 else 'above'} market"
        gap_color  = "#1A7A40" if (
            (user_type=="Buyer" and gap < 0) or
            (user_type=="Seller" and gap > 0)
        ) else "#C0392B"

        # ── Verdict card ──────────────────────────────────────────────────
        st.markdown(f"""
        <div class="{content['card_cls']}">
          <div class="verdict-icon">{content['icon']}</div>
          <div class="verdict-label {content['label_cls']}">{content['label']}</div>
          <div class="verdict-sub">{content['sub']}</div>
          <div style="margin-top:16px;font-size:22px;font-weight:700;
                      color:{gap_color};font-family:'Nunito',sans-serif;">
            ${user_price:,.0f}/ton &nbsp;·&nbsp; {gap_str}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Tip ───────────────────────────────────────────────────────────
        st.markdown(f'<div class="tip-box">{content["tip"]}</div>',
                    unsafe_allow_html=True)

        # ── Benchmark breakdown ───────────────────────────────────────────
        st.markdown('<div class="bench-card">', unsafe_allow_html=True)
        st.markdown('<div class="bench-title">Market Benchmarks</div>',
                    unsafe_allow_html=True)

        def gap_label(source_price, user_p):
            if source_price is None:
                return '<span class="bench-gap-even">—</span>'
            diff = user_p - source_price
            pct  = (diff / source_price) * 100
            sign = "+" if diff > 0 else ""
            cls  = "bench-gap-above" if diff > 0 else "bench-gap-below"
            return f'<span class="{cls}">{sign}{pct:.1f}%</span>'

        benchmarks = [
            ("🟠", "Your price",       user_price,   None,       "—"),
            ("🔵", f"HayDay model",    model_pred,   None,       f"±$24.76 accuracy"),
            ("🟢", f"USDA AMS",        usda_price,   usda_date,  "Most recent report"),
            ("🟡", f"Hoyt Report",     hoyt_price,   hoyt_date,  "Broker market report"),
            ("⚪", f"Market consensus",market_price, None,       "Weighted average"),
        ]

        for dot, source, price, dt, note in benchmarks:
            if price is None:
                continue
            date_str = f" · {dt}" if dt else ""
            gl = gap_label(price, user_price) if source != "Your price" else "—"
            st.markdown(f"""
            <div class="bench-row">
              <div>
                <span class="bench-source">{dot} <strong>{source}</strong></span><br>
                <span style="font-size:11px;color:#AAA;">{note}{date_str}</span>
              </div>
              <div style="text-align:right;">
                <div class="bench-price">${price:,.0f}/ton</div>
                <div>{gl}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Market signals ────────────────────────────────────────────────
        d = diesel.sort_values("date")
        diesel_4w = float(d.tail(4)["diesel_price"].mean())

        milk["month"] = milk["month"].astype(int)
        now = datetime.now()
        mk = milk[(milk["year"]==now.year)&(milk["month"]==now.month)]
        if mk.empty: mk = milk.sort_values(["year","month"]).tail(1)
        milk_cwt = float(mk["milk_price_cwt"].values[0])

        cattle["month"] = cattle["month"].astype(int)
        ct = cattle[(cattle["year"]==now.year)&(cattle["month"]==now.month)]
        if ct.empty: ct = cattle.sort_values(["year","month"]).tail(1)
        cof = float(ct["cattle_on_feed_ca"].values[0])

        st.markdown(f"""
        <div class="stat-row">
          <div class="stat-chip">
            <div class="stat-icon">🐄</div>
            <div class="stat-label">Cattle on feed</div>
            <div class="stat-value">{cof/1000:.0f}K head</div>
          </div>
          <div class="stat-chip">
            <div class="stat-icon">⛽</div>
            <div class="stat-label">Diesel 4w avg</div>
            <div class="stat-value">${diesel_4w:.2f}/gal</div>
          </div>
          <div class="stat-chip">
            <div class="stat-icon">🥛</div>
            <div class="stat-label">Milk price</div>
            <div class="stat-value">${milk_cwt:.2f}/cwt</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Disclaimer ────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="disclaimer">
          Market consensus from HayDay model · USDA AMS · Hoyt Reports<br>
          Week of {now.strftime('%B %d, %Y')} · {region} · {grade}
        </div>
        """, unsafe_allow_html=True)

        # ── Log to Supabase ───────────────────────────────────────────────
        _sb_insert("hay_transactions", {
            "region":       region,
            "grade":        grade,
            "user_price":   float(user_price),
            "user_type":    user_type.lower(),
            "model_price":  model_pred,
            "usda_price":   usda_price,
            "hoyt_price":   hoyt_price,
            "verdict":      verdict,
            "price_gap":    round(gap, 2),
            "gap_pct":      round(gap_pct, 2),
            "week_of":      now.date().isoformat(),
            "source":       "hayday.ai",
        })

    except Exception as e:
        st.error(f"Something went wrong: {e}")
        st.info("Try refreshing — data may still be loading.")

# ── Footer ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="powered-by">
  Powered by USDA AMS · Hoyt Hay & Pellet · NASS · EIA Diesel
</div>
""", unsafe_allow_html=True)
