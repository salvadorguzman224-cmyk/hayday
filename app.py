import os, json, time
import requests
import streamlit as st

# ── Google Drive download ────────────────────────────────────────────────────

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

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="HayDay.ai",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Nunito+Sans:wght@400;600&display=swap" rel="stylesheet">

<style>
/* ── Reset & base ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #F5F0E8 !important;
    font-family: 'Nunito Sans', sans-serif;
    color: #1C1C1E;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
footer { display: none; }
#MainMenu { display: none; }

/* ── Center & constrain layout ── */
.block-container {
    max-width: 680px !important;
    padding: 2.5rem 1.5rem 4rem !important;
    margin: 0 auto;
}

/* ── Hero heading ── */
.hayday-hero {
    text-align: center;
    padding: 3rem 0 2rem;
}
.hayday-hero .logo {
    font-family: 'Nunito', sans-serif;
    font-weight: 800;
    font-size: 2.8rem;
    color: #1C1C1E;
    letter-spacing: -0.5px;
    line-height: 1;
}
.hayday-hero .logo span {
    color: #C17F3E;
}
.hayday-hero .tagline {
    font-family: 'Nunito Sans', sans-serif;
    font-size: 1.05rem;
    color: #8B7355;
    margin-top: 0.6rem;
    font-weight: 400;
}

/* ── Input card ── */
.input-card {
    background: #FFFFFF;
    border-radius: 20px;
    padding: 2rem 2rem 1.5rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.07), 0 1px 4px rgba(0,0,0,0.04);
}
.input-card .card-label {
    font-family: 'Nunito', sans-serif;
    font-weight: 700;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #8B7355;
    margin-bottom: 0.35rem;
}

/* ── Streamlit widget overrides ── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] > div > div {
    border: 1.5px solid #E8E0D0 !important;
    border-radius: 12px !important;
    background: #FDFAF6 !important;
    font-family: 'Nunito Sans', sans-serif !important;
    font-size: 1rem !important;
    color: #1C1C1E !important;
    padding: 0.55rem 0.85rem !important;
    transition: border-color 0.15s;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: #C17F3E !important;
    box-shadow: 0 0 0 3px rgba(193,127,62,0.12) !important;
}
[data-testid="stTextInput"] label,
[data-testid="stSelectbox"] label {
    font-family: 'Nunito', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: #8B7355 !important;
}

/* ── Orange primary button ── */
[data-testid="stButton"] > button {
    background: #C17F3E !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 14px !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 0.75rem 2rem !important;
    width: 100% !important;
    margin-top: 0.75rem !important;
    cursor: pointer !important;
    transition: background 0.15s, transform 0.1s;
    letter-spacing: 0.01em;
}
[data-testid="stButton"] > button:hover {
    background: #A96B2E !important;
    transform: translateY(-1px);
}
[data-testid="stButton"] > button:active {
    transform: translateY(0);
}

/* ── Region badge shown below inputs ── */
.region-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: #FEF3E2;
    border: 1px solid #F0D9B8;
    border-radius: 999px;
    padding: 0.3rem 0.85rem;
    font-family: 'Nunito Sans', sans-serif;
    font-size: 0.85rem;
    color: #8B5E1A;
    margin-top: 0.5rem;
}

/* ── Footer ── */
.hayday-footer {
    text-align: center;
    font-family: 'Nunito Sans', sans-serif;
    font-size: 0.78rem;
    color: #B0A090;
    margin-top: 3rem;
    padding-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── ZIP → region lookup ──────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_zip_map():
    if not os.path.exists("zip_to_region.json"):
        return {}
    with open("zip_to_region.json") as f:
        return json.load(f)


def zip_to_region(zip_code: str, zip_map: dict) -> str | None:
    z = zip_code.strip()
    return zip_map.get(z) or zip_map.get(z[:5])


# ── Hero ─────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hayday-hero">
  <div class="logo">HayDay<span>.ai</span></div>
  <div class="tagline">California hay prices, predicted.</div>
</div>
""", unsafe_allow_html=True)

# ── Input card ───────────────────────────────────────────────────────────────

st.markdown('<div class="input-card">', unsafe_allow_html=True)

zip_code = st.text_input(
    "ZIP Code",
    placeholder="e.g. 93230",
    max_chars=5,
    help="Enter your California ZIP code to detect your region.",
)

grade = st.selectbox(
    "Hay Grade",
    options=["Supreme", "Premium", "Good", "Fair"],
)

delivery = st.selectbox(
    "Delivery Preference",
    options=["Delivered", "FOB Stack"],
)

# Region detection feedback
zip_map = load_zip_map()
detected_region = None

if zip_code and len(zip_code.strip()) >= 5:
    detected_region = zip_to_region(zip_code, zip_map)
    if detected_region:
        st.markdown(
            f'<div class="region-badge">📍 {detected_region}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="region-badge" style="color:#B04040;border-color:#F0C0C0;background:#FEF0F0;">'
            '⚠️ ZIP not recognized — try a CA agricultural ZIP</div>',
            unsafe_allow_html=True,
        )

get_price = st.button("Get Price →")

st.markdown('</div>', unsafe_allow_html=True)  # close .input-card

# ── Placeholder result area ───────────────────────────────────────────────────

if get_price:
    if not zip_code or len(zip_code.strip()) < 5:
        st.warning("Please enter a 5-digit ZIP code.")
    elif not detected_region:
        st.warning("ZIP code not recognized. Try a California agricultural ZIP.")
    else:
        # Prediction logic will go here in the next step
        st.info("Prediction coming soon — foundation complete.")

# ── Footer ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hayday-footer">
  Powered by USDA AMS · Open-Meteo · NASS
</div>
""", unsafe_allow_html=True)
