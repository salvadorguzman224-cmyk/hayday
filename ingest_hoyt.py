"""
ingest_hoyt.py — Hoyt Report PDF ingestion pipeline

Run in Google Colab:
    !pip install pdfplumber requests pandas
    from google.colab import drive
    drive.mount('/content/drive')
    !python ingest_hoyt.py

Or paste each function into a cell and call main() at the end.

Pipeline: download → extract → merge → validate
Outputs go to /content/drive/MyDrive/hay_market_data/
"""

import os
import re
import time
import sys
import traceback
from io import StringIO

import pandas as pd
import requests

try:
    import pdfplumber
except ImportError:
    print("pdfplumber missing — run:  pip install pdfplumber")
    sys.exit(1)


# ── Paths (Colab Drive) ──────────────────────────────────
BASE_DIR   = "/content/drive/MyDrive/hay_market_data"
PDF_DIR    = f"{BASE_DIR}/hoyt_pdfs"
MAIN_CSV   = f"{BASE_DIR}/california_hay_prices.csv"
HOYT_CSV   = f"{BASE_DIR}/hoyt_extracted.csv"
MERGED_CSV = f"{BASE_DIR}/california_hay_prices.csv"   # overwrite in place
LOG_PATH   = f"{BASE_DIR}/hoyt_manual_review.log"


# ── Constants ────────────────────────────────────────────
REPORT_DATES = [
    "041726","041026","040326","032726","031326",
    "030626","022726","022026","021326","020626",
    "013026","012326","011626","010926","010226",
    "121925","121225","120525","112125","111425",
    "103125","102425","101725","101025","100325",
    "092625","091925","091225","090525","082925",
]

HOYT_TO_REGION = {
    "California":            "Central San Joaquin Valley",
    "Central California":    "Central San Joaquin Valley",
    "Central Valley":        "Central San Joaquin Valley",
    "San Joaquin":           "Central San Joaquin Valley",
    "North San Joaquin":     "North San Joaquin Valley",
    "Sacramento Valley":     "Sacramento Valley",
    "Sacramento":            "Sacramento Valley",
    "Imperial Valley":       "Southeast",
    "Desert Southwest":      "Southeast",
    "Blythe":                "Southeast",
    "El Centro":             "Southeast",
    "Southeast":             "Southeast",
    "Intermountain":         "North Inter-Mountains",
    "Inter-Mountain":        "North Inter-Mountains",
    "North California":      "North Inter-Mountains",
}

HOYT_TO_QUALITY = {
    "Premium/Supreme":  "Premium/Supreme",
    "Good/Premium":     "Good/Premium",
    "Fair/Good":        "Fair/Good",
    "Supreme":          "Supreme",
    "Premium":          "Premium",
    "Good":             "Good",
    "Fair":             "Fair",
    "Utility":          "Utility",
}
# Sort longest keys first so "Premium/Supreme" matches before "Premium"
QUALITY_KEYS = sorted(HOYT_TO_QUALITY.keys(), key=len, reverse=True)
REGION_KEYS  = sorted(HOYT_TO_REGION.keys(),  key=len, reverse=True)

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
    "Fair":     ["Fair", "Fair/Good", "Utility/Fair"],
    "Utility":  ["Utility", "Utility/Fair"],
}

MANUAL_REVIEW = []


def _date_from_code(code):
    """'041726' → ('2026-04-17', 2026, 4)"""
    mm, dd, yy = code[0:2], code[2:4], code[4:6]
    year = 2000 + int(yy)
    return f"{year}-{mm}-{dd}", year, int(mm)


# ── 1. Download PDFs ─────────────────────────────────────
def download_hoyt_pdfs(output_dir=PDF_DIR):
    os.makedirs(output_dir, exist_ok=True)
    downloaded, skipped, failed = [], [], []

    for code in REPORT_DATES:
        date_str, year, month = _date_from_code(code)
        filename = f"The-Hoyt-Report-{code}.pdf"
        path     = os.path.join(output_dir, filename)

        if os.path.exists(path) and os.path.getsize(path) > 1000:
            skipped.append(filename)
            continue

        url = (f"https://www.thehoytreport.com/wp-content/uploads/"
               f"{year}/{month:02d}/{filename}")
        try:
            r = requests.get(url, timeout=30, headers={"User-Agent": "HayDay/1.0"})
            if r.status_code == 200 and r.content[:4] == b"%PDF":
                with open(path, "wb") as f:
                    f.write(r.content)
                print(f"  Downloaded {filename}")
                downloaded.append(filename)
            else:
                print(f"  ✖ {filename} status={r.status_code}")
                failed.append(filename)
        except Exception as e:
            print(f"  ✖ {filename} error: {e}")
            failed.append(filename)

        time.sleep(1)  # be polite

    print(f"\nDownload summary:")
    print(f"  Downloaded: {len(downloaded)}")
    print(f"  Cached:     {len(skipped)}")
    print(f"  Failed:     {len(failed)}")
    if failed:
        print(f"  Failed files: {failed}")
    return downloaded + skipped


# ── 2. Extract prices from one PDF ───────────────────────
def _parse_price_line(line):
    """Return list of dicts of (region, quality, low, high) found in a text line."""
    line_clean = line.strip()
    if len(line_clean) < 6:
        return []

    region = None
    for k in REGION_KEYS:
        if k.lower() in line_clean.lower():
            region = HOYT_TO_REGION[k]
            break
    if not region:
        return []

    quality = None
    for k in QUALITY_KEYS:
        if k.lower() in line_clean.lower():
            quality = HOYT_TO_QUALITY[k]
            break
    if not quality:
        return []

    nums = re.findall(r"\$?\s*(\d{2,3}(?:\.\d{1,2})?)", line_clean)
    plausible = [float(n) for n in nums if 50 <= float(n) <= 600]
    if len(plausible) < 2:
        return []

    low, high = sorted(plausible[:2])
    return [{"region": region, "quality": quality, "low": low, "high": high}]


def _parse_table_row(row, header_map):
    """row: list of cells; header_map: dict of column → index."""
    if not row:
        return None
    cells = [(c or "").strip() for c in row]

    region = None
    quality = None
    if "region" in header_map:
        rcell = cells[header_map["region"]]
        for k in REGION_KEYS:
            if k.lower() in rcell.lower():
                region = HOYT_TO_REGION[k]
                break
    if "quality" in header_map:
        qcell = cells[header_map["quality"]]
        for k in QUALITY_KEYS:
            if k.lower() in qcell.lower():
                quality = HOYT_TO_QUALITY[k]
                break
    if not region or not quality:
        return None

    def _num(s):
        m = re.search(r"\d{2,3}(?:\.\d{1,2})?", s)
        return float(m.group()) if m else None

    low = _num(cells[header_map["low"]])  if "low"  in header_map else None
    high = _num(cells[header_map["high"]]) if "high" in header_map else None
    if low is None or high is None:
        return None
    if low > high:
        low, high = high, low
    if not (50 <= low <= 600 and 50 <= high <= 600):
        return None
    return {"region": region, "quality": quality, "low": low, "high": high}


def _detect_header(row):
    """Return {column_name: index} based on header row, or None."""
    if not row:
        return None
    cells = [(c or "").lower().strip() for c in row]
    h = {}
    for i, c in enumerate(cells):
        if "region" in c or "area" in c or "location" in c: h.setdefault("region", i)
        if "grade" in c or "quality" in c:                   h.setdefault("quality", i)
        if c in ("low", "min", "from"):                      h.setdefault("low", i)
        if c in ("high","max", "to"):                        h.setdefault("high", i)
    return h if {"region","quality","low","high"} <= set(h) else None


def extract_hoyt_prices(pdf_path, report_date_code):
    date_str, *_ = _date_from_code(report_date_code)
    rows = []
    seen = set()  # (region, quality, low, high) dedup within one PDF

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Strategy A: tables
                try:
                    for table in (page.extract_tables() or []):
                        if not table:
                            continue
                        header_map = _detect_header(table[0])
                        if header_map:
                            for row in table[1:]:
                                parsed = _parse_table_row(row, header_map)
                                if parsed:
                                    rows.append(parsed)
                except Exception:
                    pass

                # Strategy B: text line scan
                try:
                    text = page.extract_text() or ""
                    for line in text.split("\n"):
                        rows.extend(_parse_price_line(line))
                except Exception:
                    pass
    except Exception as e:
        MANUAL_REVIEW.append((os.path.basename(pdf_path), str(e)))
        return []

    # Dedup + format
    out = []
    for r in rows:
        key = (r["region"], r["quality"], r["low"], r["high"])
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "date":         date_str,
            "state":        "California",
            "region":       r["region"],
            "commodity":    "Hay",
            "quality":      r["quality"],
            "price_avg":    round((r["low"] + r["high"]) / 2, 1),
            "price_min":    r["low"],
            "price_max":    r["high"],
            "is_alfalfa":   1,
            "is_delivered": 0,
            "source":       "Hoyt Report",
            "desc":         f"Hoyt Report {report_date_code}",
        })
    return out


# ── 3. Process all PDFs ──────────────────────────────────
def process_all_hoyt_pdfs(pdf_dir=PDF_DIR, intermediate_csv=HOYT_CSV):
    all_rows = []
    files = sorted(f for f in os.listdir(pdf_dir) if f.endswith(".pdf"))
    print(f"\nProcessing {len(files)} PDFs from {pdf_dir}")

    for filename in files:
        m = re.search(r"(\d{6})\.pdf$", filename)
        if not m:
            print(f"  ⊘ Cannot parse date from {filename}")
            MANUAL_REVIEW.append((filename, "filename has no MMDDYY"))
            continue
        code = m.group(1)
        path = os.path.join(pdf_dir, filename)
        try:
            extracted = extract_hoyt_prices(path, code)
            all_rows.extend(extracted)
            print(f"  Extracted {len(extracted):>3} rows from {filename}")
            if not extracted:
                MANUAL_REVIEW.append((filename, "no rows extracted"))
            # Save intermediate after each PDF
            pd.DataFrame(all_rows).to_csv(intermediate_csv, index=False)
        except Exception as e:
            print(f"  ✖ Failed {filename}: {e}")
            MANUAL_REVIEW.append((filename, traceback.format_exc(limit=2)))

    df_hoyt = pd.DataFrame(all_rows)
    print(f"\nExtraction summary:")
    print(f"  Total rows extracted: {len(df_hoyt)}")
    if len(df_hoyt):
        print(f"  Date range: {df_hoyt['date'].min()} → {df_hoyt['date'].max()}")
        print(f"  Price range: ${df_hoyt['price_avg'].min():.0f} → ${df_hoyt['price_avg'].max():.0f}")
        print(f"  Avg price: ${df_hoyt['price_avg'].mean():.0f}")
        print(f"\nBy region:")
        print(df_hoyt["region"].value_counts().to_string())
        print(f"\nBy quality:")
        print(df_hoyt["quality"].value_counts().to_string())
    return df_hoyt


# ── 4. Merge with main dataset ───────────────────────────
def merge_hoyt_data(hoyt_df, main_csv=MAIN_CSV, output_csv=MERGED_CSV):
    df_main = pd.read_csv(main_csv)
    df_main["date"]  = pd.to_datetime(df_main["date"])
    if "source" not in df_main.columns:
        df_main["source"] = "USDA AMS"
    df_main["source"] = df_main["source"].fillna("USDA AMS")

    if hoyt_df is None or len(hoyt_df) == 0:
        print("No Hoyt rows to merge — leaving main CSV untouched.")
        return df_main

    hoyt_df = hoyt_df.copy()
    hoyt_df["date"] = pd.to_datetime(hoyt_df["date"])
    for col in df_main.columns:
        if col not in hoyt_df.columns:
            hoyt_df[col] = None
    hoyt_df = hoyt_df[df_main.columns]

    df_combined = pd.concat([df_main, hoyt_df], ignore_index=True)

    # USDA AMS wins on collisions: sort so USDA appears first within
    # each (date, region, quality), then drop_duplicates(keep='first')
    df_combined["_src_rank"] = (df_combined["source"] != "USDA AMS").astype(int)
    df_combined = (df_combined
                   .sort_values(["date","region","quality","_src_rank"])
                   .drop_duplicates(subset=["date","region","quality"], keep="first")
                   .drop(columns=["_src_rank"])
                   .reset_index(drop=True))

    df_combined.to_csv(output_csv, index=False)

    n_usda = (df_combined["source"] == "USDA AMS").sum()
    n_hoyt = (df_combined["source"] == "Hoyt Report").sum()
    cutoff = df_combined["date"].max() - pd.Timedelta(weeks=13)
    ca13 = df_combined[
        (df_combined["state"] == "California") &
        (df_combined["commodity"] == "Hay") &
        (df_combined["region"].isin(CA_VALID_REGIONS)) &
        (df_combined["date"] >= cutoff)
    ]
    print(f"\nMerge summary:")
    print(f"  USDA AMS records:    {n_usda:,}")
    print(f"  Hoyt Report records: {n_hoyt:,}")
    print(f"  Total combined:      {len(df_combined):,}")
    print(f"  CA Hay records (13w):{len(ca13):,}")
    if len(ca13):
        print(f"  CA Hay avg (13w):    ${ca13['price_avg'].mean():.0f}/ton")
    return df_combined


# ── 5. Validate ──────────────────────────────────────────
def validate_dataset(csv_path=MERGED_CSV):
    df = pd.read_csv(csv_path)
    df["date"]      = pd.to_datetime(df["date"])
    df["price_avg"] = pd.to_numeric(df["price_avg"], errors="coerce")
    if "source" not in df.columns:
        df["source"] = ""

    cutoff = df["date"].max() - pd.Timedelta(weeks=13)
    ca = df[
        (df["state"]     == "California") &
        (df["commodity"] == "Hay") &
        (df["region"].isin(CA_VALID_REGIONS))
    ]
    ca13 = ca[ca["date"] >= cutoff]

    def _avg(mask):
        d = ca13[mask]
        return (d["price_avg"].mean(), len(d))

    prem_avg, prem_n = _avg(
        ca13["quality"].isin(QUALITY_MATCH["Premium"]) & (ca13["is_alfalfa"] == 1)
    )
    good_avg, good_n = _avg(
        ca13["quality"].isin(QUALITY_MATCH["Good"]) & (ca13["is_alfalfa"] == 1)
    )

    low_hay     = (df["commodity"] == "Hay") & (df["price_avg"] < 80)
    ca_invalid  = (df["state"] == "California") & (~df["region"].isin(CA_VALID_REGIONS))
    nass_rows   = df["desc"].astype(str).str.contains("NASS", na=False).sum() if "desc" in df.columns else 0
    hoyt_rows   = (df["source"] == "Hoyt Report").sum()

    def s(ok): return "✅" if ok else "❌"
    print("\nVALIDATION")
    print("=" * 50)
    print(f"  {s(190 <= prem_avg <= 270)} Premium alfalfa avg $190-270/ton  (got ${prem_avg:.0f}, n={prem_n})")
    print(f"  {s(140 <= good_avg <= 220)} Good alfalfa avg $140-220/ton     (got ${good_avg:.0f}, n={good_n})")
    print(f"  {s(low_hay.sum() == 0)} No CA Hay prices under $80/ton    (found {low_hay.sum()})")
    print(f"  {s(ca_invalid.sum() == 0)} All CA rows in 5 valid regions    (invalid: {ca_invalid.sum()})")
    print(f"  {s(nass_rows == 0)} No NASS rows                      (found {nass_rows})")
    print(f"  {s(hoyt_rows > 0)} Hoyt rows present                 (count: {hoyt_rows})")
    print(f"  {s(len(ca13) > 100)} CA 13-week records > 100         (got {len(ca13)})")


# ── Main ─────────────────────────────────────────────────
def main():
    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(PDF_DIR, exist_ok=True)

    print("STEP 1 — Download PDFs")
    download_hoyt_pdfs(PDF_DIR)

    print("\nSTEP 2-3 — Extract & process PDFs")
    df_hoyt = process_all_hoyt_pdfs(PDF_DIR, HOYT_CSV)

    print("\nSTEP 4 — Merge with main dataset")
    merge_hoyt_data(df_hoyt, MAIN_CSV, MERGED_CSV)

    print("\nSTEP 5 — Validate")
    validate_dataset(MERGED_CSV)

    if MANUAL_REVIEW:
        print(f"\nManual review needed for {len(MANUAL_REVIEW)} PDFs:")
        with open(LOG_PATH, "w") as f:
            for name, reason in MANUAL_REVIEW:
                line = f"{name}: {reason.splitlines()[0]}"
                print(f"  {line}")
                f.write(line + "\n")
        print(f"Log written to {LOG_PATH}")
    else:
        print("\n✅ All PDFs parsed automatically — no manual review needed.")


if __name__ == "__main__":
    main()
