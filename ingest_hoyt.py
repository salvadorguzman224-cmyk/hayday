"""
ingest_hoyt.py — Hoyt Report PDF → california_hay_prices.csv

Run in Google Colab:
  !pip install pdfplumber requests pandas
  from google.colab import drive
  drive.mount('/content/drive')
  !git clone https://github.com/salvadorguzman224-cmyk/hayday.git /content/hayday
  !python /content/hayday/ingest_hoyt.py

Standalone monthly ETL — not imported by app.py. Downloads the weekly
Hoyt Report PDFs, parses CA price tables, merges into the main dataset,
and validates the result.
"""

from __future__ import annotations

import os
import re
import sys
import time
import subprocess
import traceback
from datetime import datetime

import pandas as pd
import requests

# pdfplumber may not be installed — try to install before importing
try:
    import pdfplumber  # noqa: F401
except ImportError:
    print("pdfplumber not found — installing…")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pdfplumber"], check=True)
    import pdfplumber  # noqa: F401


# ── Paths ────────────────────────────────────────────────
DRIVE_DIR  = "/content/drive/MyDrive/hay_market_data"
PDF_DIR    = f"{DRIVE_DIR}/hoyt_pdfs"
MAIN_CSV   = f"{DRIVE_DIR}/california_hay_prices.csv"
OUTPUT_CSV = f"{DRIVE_DIR}/california_hay_prices.csv"
INTERIM_CSV = f"{DRIVE_DIR}/hoyt_extracted_interim.csv"
LOG_FILE   = f"{DRIVE_DIR}/hoyt_manual_review.log"


# ── Constants ────────────────────────────────────────────
REPORT_CODES = [
    "041726","041026","040326","032726","031326",
    "030626","022726","022026","021326","020626",
    "013026","012326","011626","010926","010226",
    "121925","121225","120525","112125","111425",
    "103125","102425","101725","101025","100325",
    "092625","091925","091225","090525","082925",
]

HOYT_TO_REGION = {
    "northern california":  "North Inter-Mountains",
    "north san joaquin":    "North San Joaquin Valley",
    "central california":   "Central San Joaquin Valley",
    "central valley":       "Central San Joaquin Valley",
    "sacramento valley":    "Sacramento Valley",
    "imperial valley":      "Southeast",
    "desert southwest":     "Southeast",
    "inter-mountain":       "North Inter-Mountains",
    "intermountain":        "North Inter-Mountains",
    "san joaquin":          "Central San Joaquin Valley",
    "sacramento":           "Sacramento Valley",
    "el centro":            "Southeast",
    "coachella":            "Southeast",
    "southeast":            "Southeast",
    "california":           "Central San Joaquin Valley",
    "blythe":               "Southeast",
    "modoc":                "North Inter-Mountains",
}
# Sort longest first so multi-word keys match before short prefixes
REGION_KEYS = sorted(HOYT_TO_REGION.keys(), key=len, reverse=True)

HOYT_TO_QUALITY = {
    "premium/supreme":  "Premium/Supreme",
    "good/premium":     "Good/Premium",
    "fair/good":        "Fair/Good",
    "utility/fair":     "Utility/Fair",
    "supreme":          "Supreme",
    "premium":          "Premium",
    "good":             "Good",
    "fair":             "Fair",
    "utility":          "Utility",
}
QUALITY_KEYS = sorted(HOYT_TO_QUALITY.keys(), key=len, reverse=True)

CA_VALID_REGIONS = [
    "Central San Joaquin Valley",
    "North San Joaquin Valley",
    "Sacramento Valley",
    "North Inter-Mountains",
    "Southeast",
]

PRICE_MIN, PRICE_MAX = 80, 600
MANUAL_REVIEW: list[tuple[str, str]] = []


# ── Helpers ──────────────────────────────────────────────
def _log_failure(filename: str, reason: str) -> None:
    """Append timestamped failure to LOG_FILE and in-memory list."""
    MANUAL_REVIEW.append((filename, reason))
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')}  "
                    f"{filename}: {reason.splitlines()[0][:200]}\n")
    except Exception:
        pass


def _date_from_code(code: str) -> str:
    """'041726' → '2026-04-17'."""
    mm, dd, yy = code[0:2], code[2:4], code[4:6]
    return f"{2000 + int(yy)}-{mm}-{dd}"


def _map_region(text: str) -> str | None:
    t = text.lower()
    for key in REGION_KEYS:
        if key in t:
            return HOYT_TO_REGION[key]
    return None


def _map_quality(text: str) -> str | None:
    t = text.lower()
    for key in QUALITY_KEYS:
        if key in t:
            return HOYT_TO_QUALITY[key]
    return None


def _extract_prices_in_range(text: str) -> list[float]:
    """Pull plausible $80-$600 numbers from a string."""
    return [
        float(n) for n in re.findall(r"\d{2,3}(?:\.\d{1,2})?", text)
        if PRICE_MIN <= float(n) <= PRICE_MAX
    ]


# ── 1. Download PDFs ─────────────────────────────────────
def download_hoyt_pdfs() -> list[str]:
    os.makedirs(PDF_DIR, exist_ok=True)
    downloaded: list[str] = []
    cached:     list[str] = []
    failed:     list[str] = []

    print(f"\n[1/5] Downloading {len(REPORT_CODES)} Hoyt Report PDFs…")
    for code in REPORT_CODES:
        mm, _, yy = code[0:2], code[2:4], code[4:6]
        year   = 2000 + int(yy)
        path   = os.path.join(PDF_DIR, f"hoyt_{code}.pdf")

        if os.path.exists(path) and os.path.getsize(path) > 1000:
            cached.append(code)
            continue

        url = (f"https://www.thehoytreport.com/wp-content/uploads/"
               f"{year}/{mm}/The-Hoyt-Report-{code}.pdf")
        try:
            r = requests.get(url, timeout=30, headers={"User-Agent": "HayDay/1.0"})
            if r.status_code == 200 and r.content[:4] == b"%PDF":
                with open(path, "wb") as f:
                    f.write(r.content)
                print(f"  ✅ Downloaded hoyt_{code}.pdf  ({len(r.content)//1024} KB)")
                downloaded.append(code)
            else:
                msg = f"HTTP {r.status_code}"
                print(f"  ✖ hoyt_{code}.pdf — {msg}")
                _log_failure(f"hoyt_{code}.pdf", f"download {msg}")
                failed.append(code)
        except Exception as e:
            print(f"  ✖ hoyt_{code}.pdf — {e}")
            _log_failure(f"hoyt_{code}.pdf", f"download exception: {e}")
            failed.append(code)

        time.sleep(1)  # respectful pacing

    print(f"\nDownloaded: {len(downloaded)}  ·  Cached: {len(cached)}  ·  Failed: {len(failed)}")
    return downloaded + cached


# ── 2. Extract from one PDF ──────────────────────────────
_TEXT_FALLBACK_RE = re.compile(
    r"([A-Za-z /\-]{4,40}?)"                                        # region words
    r"\s+(Supreme|Premium|Good|Fair|Utility|"
    r"Premium/Supreme|Good/Premium|Fair/Good|Utility/Fair)"          # grade
    r"[^\d]*"
    r"(\d{2,3})\s*[-–]\s*(\d{2,3})",                                 # low–high
    re.IGNORECASE,
)


def extract_hoyt_prices(pdf_path: str, report_date: str) -> list[dict]:
    import pdfplumber  # late re-import for safety in notebook reruns

    filename = os.path.basename(pdf_path)
    rows_a:  list[dict] = []
    rows_b:  list[dict] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Strategy A — table extraction
                try:
                    for table in (page.extract_tables() or []):
                        for row in table:
                            if not row or len(row) < 3:
                                continue
                            cells = [(c or "").strip() for c in row]
                            region  = _map_region(cells[0])
                            quality = _map_quality(cells[1]) if len(cells) > 1 else None
                            if not region or not quality:
                                continue
                            tail = " ".join(cells[2:])
                            prices = _extract_prices_in_range(tail)
                            if not prices:
                                continue
                            if len(prices) >= 2:
                                lo, hi = min(prices[:2]), max(prices[:2])
                            else:
                                lo = hi = prices[0]
                            rows_a.append({
                                "region": region, "quality": quality,
                                "lo": lo, "hi": hi,
                            })
                except Exception:
                    pass

                # Strategy B — text regex (only used if A finds nothing)
                try:
                    text = page.extract_text() or ""
                    for m in _TEXT_FALLBACK_RE.finditer(text):
                        region  = _map_region(m.group(1))
                        quality = _map_quality(m.group(2))
                        lo, hi = float(m.group(3)), float(m.group(4))
                        if not region or not quality:
                            continue
                        if not (PRICE_MIN <= lo <= PRICE_MAX and PRICE_MIN <= hi <= PRICE_MAX):
                            continue
                        if lo > hi:
                            lo, hi = hi, lo
                        rows_b.append({
                            "region": region, "quality": quality,
                            "lo": lo, "hi": hi,
                        })
                except Exception:
                    pass
    except Exception as e:
        _log_failure(filename, f"open/parse failed: {e}")
        return []

    rows = rows_a if rows_a else rows_b

    # Dedup by (region, quality) — keep first occurrence
    seen: set[tuple[str, str]] = set()
    out: list[dict] = []
    for r in rows:
        key = (r["region"], r["quality"])
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "date":         report_date,
            "state":        "California",
            "region":       r["region"],
            "commodity":    "Hay",
            "quality":      r["quality"],
            "price_avg":    round((r["lo"] + r["hi"]) / 2, 1),
            "price_min":    r["lo"],
            "price_max":    r["hi"],
            "is_alfalfa":   1,
            "is_delivered": 0,
            "source":       "Hoyt Report",
            "desc":         f"Hoyt {filename}",
        })
    return out


# ── 3. Process all PDFs ──────────────────────────────────
def process_all_hoyt_pdfs() -> pd.DataFrame:
    print(f"\n[2/5] Extracting prices from PDFs in {PDF_DIR}…")
    all_rows: list[dict] = []

    for code in REPORT_CODES:
        path = os.path.join(PDF_DIR, f"hoyt_{code}.pdf")
        if not os.path.exists(path):
            print(f"  ⊘ hoyt_{code}.pdf — not downloaded, skipping")
            _log_failure(f"hoyt_{code}.pdf", "PDF missing on disk")
            continue

        date_str = _date_from_code(code)
        try:
            rows = extract_hoyt_prices(path, date_str)
        except Exception as e:
            print(f"  ✖ hoyt_{code}.pdf — extract crashed: {e}")
            _log_failure(f"hoyt_{code}.pdf", traceback.format_exc(limit=2))
            continue

        if rows:
            all_rows.extend(rows)
            print(f"  ✅ {code} — {len(rows):>2} rows")
        else:
            print(f"  ⚠ {code} — 0 rows extracted (manual review)")
            _log_failure(f"hoyt_{code}.pdf", "no rows extracted")

        # Crash-safe interim save after every PDF
        try:
            pd.DataFrame(all_rows).to_csv(INTERIM_CSV, index=False)
        except Exception:
            pass

    df = pd.DataFrame(all_rows)
    print(f"\nExtraction summary:")
    print(f"  Total rows:   {len(df)}")
    if len(df):
        print(f"  Date range:   {df['date'].min()} → {df['date'].max()}")
        print(f"  Price range:  ${df['price_avg'].min():.0f} → ${df['price_avg'].max():.0f}")
        print(f"  Avg price:    ${df['price_avg'].mean():.0f}")
        print(f"\n  By region:")
        for region, n in df["region"].value_counts().items():
            print(f"    {region:<32} {n}")
        print(f"\n  By quality:")
        for quality, n in df["quality"].value_counts().items():
            print(f"    {quality:<20} {n}")

    if MANUAL_REVIEW:
        print(f"\nManual review needed for {len(MANUAL_REVIEW)} files — see {LOG_FILE}")
    return df


# ── 4. Merge with main CSV ───────────────────────────────
def merge_hoyt_data(df_hoyt: pd.DataFrame) -> pd.DataFrame:
    print(f"\n[3/5] Merging with {MAIN_CSV}…")
    df_main = pd.read_csv(MAIN_CSV)
    df_main["date"] = pd.to_datetime(df_main["date"])

    if "source" not in df_main.columns:
        df_main["source"] = "USDA AMS"
    df_main["source"] = df_main["source"].fillna("USDA AMS")

    if df_hoyt is None or len(df_hoyt) == 0:
        print("  No Hoyt rows to merge — main CSV unchanged.")
        return df_main

    df_hoyt = df_hoyt.copy()
    df_hoyt["date"] = pd.to_datetime(df_hoyt["date"])
    for col in df_main.columns:
        if col not in df_hoyt.columns:
            df_hoyt[col] = None
    df_hoyt = df_hoyt[df_main.columns]

    # Concat then dedup — USDA AMS wins (rank 0) over Hoyt (rank 1)
    combined = pd.concat([df_main, df_hoyt], ignore_index=True)
    combined["_rank"] = (combined["source"] != "USDA AMS").astype(int)
    combined = (combined
                .sort_values(["date", "region", "quality", "commodity", "_rank"])
                .drop_duplicates(subset=["date", "region", "quality", "commodity"], keep="first")
                .drop(columns=["_rank"])
                .reset_index(drop=True))

    combined.to_csv(OUTPUT_CSV, index=False)

    n_ams  = (combined["source"] == "USDA AMS").sum()
    n_hoyt = (combined["source"] == "Hoyt Report").sum()
    cutoff = combined["date"].max() - pd.Timedelta(weeks=13)
    ca13 = combined[
        (combined["state"]     == "California") &
        (combined["commodity"] == "Hay") &
        (combined["region"].isin(CA_VALID_REGIONS)) &
        (combined["date"] >= cutoff)
    ]
    print(f"  USDA AMS records:    {n_ams:,}")
    print(f"  Hoyt records:        {n_hoyt:,}")
    print(f"  Combined total:      {len(combined):,}")
    print(f"  CA Hay records (13w): {len(ca13):,}")
    if len(ca13):
        print(f"  CA Hay avg (13w):    ${ca13['price_avg'].mean():.0f}/ton")
    return combined


# ── 5. Validate ──────────────────────────────────────────
def validate_dataset(df: pd.DataFrame) -> None:
    print(f"\n[4/5] Validation")
    print("=" * 56)

    df = df.copy()
    df["date"]      = pd.to_datetime(df["date"])
    df["price_avg"] = pd.to_numeric(df["price_avg"], errors="coerce")
    if "source" not in df.columns:
        df["source"] = ""
    if "desc" not in df.columns:
        df["desc"] = ""

    cutoff = df["date"].max() - pd.Timedelta(weeks=13)
    ca = df[
        (df["state"]     == "California") &
        (df["commodity"] == "Hay") &
        (df["region"].isin(CA_VALID_REGIONS))
    ]
    ca13 = ca[ca["date"] >= cutoff]

    prem = ca13[
        ca13["quality"].isin(["Premium", "Good/Premium", "Premium/Supreme"]) &
        (ca13["is_alfalfa"] == 1)
    ]
    good = ca13[
        ca13["quality"].isin(["Good", "Fair/Good"]) &
        (ca13["is_alfalfa"] == 1)
    ]

    prem_avg = prem["price_avg"].mean() if len(prem) else 0
    good_avg = good["price_avg"].mean() if len(good) else 0

    low_hay    = ((df["commodity"] == "Hay") & (df["price_avg"] < 80)).sum()
    ca_invalid = ((df["state"] == "California") & (~df["region"].isin(CA_VALID_REGIONS))).sum()
    nass_rows  = df["desc"].astype(str).str.contains("NASS", case=False, na=False).sum()
    hoyt_rows  = (df["source"] == "Hoyt Report").sum()

    def s(ok: bool) -> str: return "✅" if ok else "❌"

    checks = [
        (190 <= prem_avg <= 270,
         f"Premium alfalfa avg $190-270/ton  (got ${prem_avg:.0f}, n={len(prem)})"),
        (140 <= good_avg <= 220,
         f"Good alfalfa avg $140-220/ton     (got ${good_avg:.0f}, n={len(good)})"),
        (low_hay == 0,
         f"No CA Hay prices under $80/ton    (found {low_hay})"),
        (ca_invalid == 0,
         f"All CA rows in 5 valid regions    (invalid: {ca_invalid})"),
        (nass_rows == 0,
         f"No NASS rows                      (found {nass_rows})"),
        (hoyt_rows > 0,
         f"Hoyt rows present                 (count: {hoyt_rows})"),
        (len(ca13) > 100,
         f"CA 13-week records > 100          (got {len(ca13)})"),
    ]
    for ok, msg in checks:
        print(f"  {s(ok)} {msg}")

    n_pass = sum(1 for ok, _ in checks if ok)
    print(f"\n  {n_pass}/{len(checks)} checks passing")


# ── 6. Main ──────────────────────────────────────────────
def main() -> None:
    # Mount Drive if running in Colab and not already mounted
    if not os.path.exists("/content/drive/MyDrive"):
        try:
            from google.colab import drive  # type: ignore
            drive.mount("/content/drive")
        except Exception:
            print("Note: not running in Colab — make sure DRIVE_DIR is reachable.")

    os.makedirs(DRIVE_DIR, exist_ok=True)
    os.makedirs(PDF_DIR,   exist_ok=True)

    print(f"Hoyt Report ETL — {datetime.now().isoformat(timespec='seconds')}")
    print(f"Output: {DRIVE_DIR}")

    download_hoyt_pdfs()

    df_hoyt = process_all_hoyt_pdfs()

    if len(df_hoyt) == 0:
        print("\nNo data extracted — see manual review log:")
        print(f"  {LOG_FILE}")
        return

    df_combined = merge_hoyt_data(df_hoyt)
    validate_dataset(df_combined)

    print(f"\n[5/5] Done.  Merged CSV: {OUTPUT_CSV}")
    if MANUAL_REVIEW:
        print(f"      Manual review: {len(MANUAL_REVIEW)} files in {LOG_FILE}")


if __name__ == "__main__":
    main()
