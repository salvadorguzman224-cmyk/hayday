"""
Quick API connectivity check — run this to verify all your keys work.
Usage: python scripts/check_apis.py
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

USDA_AMS_KEY  = os.getenv("USDA_AMS_API_KEY", "")
USDA_NASS_KEY = os.getenv("USDA_NASS_API_KEY", "")
NOAA_KEY      = os.getenv("NOAA_API_KEY", "")
EIA_KEY       = os.getenv("EIA_API_KEY", "")

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):     print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg):   print(f"  {RED}✗{RESET} {msg}")
def warn(msg):   print(f"  {YELLOW}⚠{RESET} {msg}")
def info(msg):   print(f"    {msg}")
def header(msg): print(f"\n{BOLD}{msg}{RESET}")


async def check_usda_ams():
    header("USDA AMS Market News  (CA Direct Hay)")
    if not USDA_AMS_KEY:
        warn("USDA_AMS_API_KEY not set — skipping")
        return False

    # MARS API uses HTTP Basic Auth: api_key as username, empty password
    _auth = (USDA_AMS_KEY, "")

    try:
        async with httpx.AsyncClient(timeout=20.0) as c:
            # Step 1: confirm base URL is reachable with auth
            r = await c.get(
                "https://marsapi.ams.usda.gov/services/v1.2/reports",
                auth=_auth,
            )
            if r.status_code == 401:
                fail("401 Unauthorized — USDA_AMS_API_KEY is invalid")
                return False
            if r.status_code == 403:
                fail(f"403 Forbidden — key may be inactive or IP blocked\n    {r.text[:200]}")
                return False
            if r.status_code not in (200, 404):
                fail(f"HTTP {r.status_code}: {r.text[:120]}")
                return False

            # Step 2: search for CA Direct Hay report slug
            r2 = await c.get(
                "https://marsapi.ams.usda.gov/services/v1.2/reports",
                auth=_auth,
                params={"q": "California Direct Hay"},
            )
            if r2.status_code == 200:
                results = r2.json() if isinstance(r2.json(), list) else r2.json().get("results", [])
                slugs = [r.get("slug_id") or r.get("report_title", "") for r in results[:3]]
                if results:
                    ok(f"Connected — found {len(results)} report(s). First slugs: {slugs}")
                    slug = results[0].get("slug_id", "LM_GR212")
                    r3 = await c.get(
                        f"https://marsapi.ams.usda.gov/services/v1.2/reports/{slug}",
                        auth=_auth,
                        params={"allSections": "true"},
                    )
                    if r3.status_code == 200:
                        data = r3.json()
                        count = len(data) if isinstance(data, list) else len(data.get("results", []))
                        ok(f"Fetched report '{slug}' — {count} records")
                    return True
                else:
                    r3 = await c.get(
                        "https://marsapi.ams.usda.gov/services/v1.2/reports/LM_GR212",
                        auth=_auth,
                        params={"allSections": "true"},
                    )
                    if r3.status_code == 200:
                        ok("Connected — LM_GR212 report fetched successfully")
                        return True
                    elif r3.status_code == 404:
                        warn("Key valid but LM_GR212 returned 404 — searching for current slug…")
                        r4 = await c.get(
                            "https://marsapi.ams.usda.gov/services/v1.2/reports",
                            auth=_auth,
                            params={"q": "hay"},
                        )
                        if r4.status_code == 200:
                            hay_reports = r4.json() if isinstance(r4.json(), list) else r4.json().get("results", [])
                            ca_reports = [
                                r.get("slug_id", "") for r in hay_reports
                                if "california" in str(r).lower() or "CA" in str(r)
                            ]
                            info(f"Hay reports found: {[r.get('slug_id') for r in hay_reports[:5]]}")
                            info(f"CA-related: {ca_reports[:5]}")
                            warn("Key valid. Update REPORT_SLUG in usda_ams.py with the slug above.")
                        return True
            else:
                fail(f"HTTP {r2.status_code}: {r2.text[:120]}")
    except Exception as e:
        fail(f"Connection error: {type(e).__name__}: {e}")
    return False


async def check_usda_nass():
    header("USDA NASS Quick Stats  (CA hay production)")
    if not USDA_NASS_KEY:
        warn("USDA_NASS_API_KEY not set — skipping")
        return False

    base = "https://quickstats.nass.usda.gov/api"

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as c:
            # Step 1: lightweight key test — get_param_values needs only 'key' + 'param'
            r_pv = await c.get(
                f"{base}/get_param_values",
                params={"key": USDA_NASS_KEY, "param": "commodity_desc"},
            )

        if r_pv.status_code == 200:
            commodities = r_pv.json().get("commodity_desc", [])
            ok(f"Key valid — get_param_values returned {len(commodities)} commodities")

            # Use exact year — NASS counts/GET do not support __GE comparison operators.
            # Production ingestion already uses exact year=str(year) calls per year.
            data_params = {
                "key": USDA_NASS_KEY,
                "source_desc": "SURVEY",
                "commodity_desc": "HAY",
                "statisticcat_desc": "PRODUCTION",
                "agg_level_desc": "STATE",
                "state_alpha": "CA",
                "year": "2024",
                "format": "JSON",
            }

            # Step 2a: counts endpoint — lightweight, tells us if params are valid
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as c:
                r_cnt = await c.get(f"{base}/counts", params=data_params)

            if r_cnt.status_code == 200:
                n = r_cnt.json().get("count", "?")
                ok(f"counts endpoint — {n} CA hay production records for 2024")
                # Step 2b: actual data fetch
                async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as c:
                    r = await c.get(f"{base}/GET", params=data_params)
                if r.status_code == 200:
                    count = len(r.json().get("data", []))
                    ok(f"Data endpoint — {count} CA hay production record(s) fetched")
                else:
                    warn(f"counts={n} but GET returned {r.status_code}: {r.text[:200]}")
                    info("  → Data confirmed to exist; NASS may block bulk GET from cloud IPs")
                    info("  → Ingestion will work from a non-cloud server/local machine")
            else:
                warn(f"counts endpoint returned {r_cnt.status_code}: {r_cnt.text[:200]}")
            return True

        elif r_pv.status_code in (403, 404):
            body = r_pv.text[:400]
            fail(f"HTTP {r_pv.status_code} on get_param_values: {body}")
            info("  → NASS API key not yet active — keys can take 24–48 h after email confirmation")
            info("  → Log in at quickstats.nass.usda.gov and ensure your account is approved")
            info("  → NASS sometimes blocks Colab/GCP IPs; test from a local machine if issue persists")
        else:
            fail(f"HTTP {r_pv.status_code}: {r_pv.text[:300]}")
    except Exception as e:
        fail(f"Connection error: {type(e).__name__}: {e}")
    return False


async def check_noaa():
    header("NOAA Climate Data Online  (weather stations)")
    if not NOAA_KEY:
        warn("NOAA_API_KEY not set — skipping")
        return False

    url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/stations/GHCND:USW00023232"
    headers = {"token": NOAA_KEY}
    try:
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.get(url, headers=headers)
        if r.status_code == 200:
            name = r.json().get("name", "unknown station")
            ok(f"Connected — station: {name}")
            return True
        elif r.status_code == 400:
            fail("400 — Invalid token (check your NOAA_API_KEY)")
        elif r.status_code == 429:
            warn("429 Rate limited — key is valid but you've hit the NOAA hourly limit")
            return True
        else:
            fail(f"HTTP {r.status_code}: {r.text[:120]}")
    except Exception as e:
        fail(f"Connection error: {e}")
    return False


async def check_eia():
    header("EIA Open Data  (CA diesel prices)")
    if not EIA_KEY:
        warn("EIA_API_KEY not set — skipping")
        return False

    # Step 1: ping the root endpoint to verify key is active
    try:
        async with httpx.AsyncClient(timeout=15.0) as c:
            r_ping = await c.get(
                "https://api.eia.gov/v2/",
                params={"api_key": EIA_KEY},
            )

        if r_ping.status_code == 200:
            # Step 2: fetch CA diesel prices
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(
                    "https://api.eia.gov/v2/petroleum/pri/gnd/data/",
                    params={
                        "api_key": EIA_KEY,
                        "frequency": "weekly",
                        "data[0]": "value",
                        "facets[product][]": "EPD2DXL0",
                        "facets[duoarea][]": "SCA",   # EIA v2 uses duoarea not area
                        "length": 1,
                    },
                )
            if r.status_code == 200:
                records = r.json().get("response", {}).get("data", [])
                if records:
                    latest = records[0]
                    ok(f"Connected — latest CA diesel: ${latest.get('value','?')}/gal ({latest.get('period','?')})")
                else:
                    warn("Connected but no records — key valid, data may be temporarily unavailable")
                return True
            else:
                fail(f"Prices endpoint HTTP {r.status_code}: {r.text[:120]}")
        elif r_ping.status_code in (400, 403):
            # EIA returns 400 with error message for invalid keys
            body = r_ping.text[:300]
            if "invalid" in body.lower() or "not found" in body.lower():
                fail(f"Invalid API key — check EIA_API_KEY\n    {body}")
            else:
                warn(f"Key may still be activating (EIA keys take ~15 min after registration)\n    HTTP {r_ping.status_code}: {body}")
        else:
            fail(f"HTTP {r_ping.status_code}: {r_ping.text[:120]}")
    except Exception as e:
        fail(f"Connection error: {e}")
    return False


async def main():
    print(f"\n{BOLD}{'='*50}")
    print("  Hay Price Predictor — API Key Check")
    print(f"{'='*50}{RESET}")

    results = await asyncio.gather(
        check_usda_ams(),
        check_usda_nass(),
        check_noaa(),
        check_eia(),
    )

    passed  = sum(1 for r in results if r)
    skipped = sum(1 for k in [USDA_AMS_KEY, USDA_NASS_KEY, NOAA_KEY, EIA_KEY] if not k)
    failed  = 4 - passed - skipped

    print(f"\n{BOLD}{'='*50}{RESET}")
    print(f"  {GREEN}{passed} passed{RESET}  |  {YELLOW}{skipped} skipped{RESET}  |  {RED}{failed} failed{RESET}")
    print()

    if passed == 4:
        print(f"  {GREEN}{BOLD}All APIs ready!{RESET}")
        print("  docker-compose up --build   ← start everything")
        print("  curl -X POST http://localhost:8000/api/v1/ingestion/trigger/usda_ams")
    elif failed:
        print(f"  {RED}Fix the failing keys above, then re-run this script.{RESET}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
