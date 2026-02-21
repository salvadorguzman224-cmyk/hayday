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

def ok(msg):    print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg):  print(f"  {RED}✗{RESET} {msg}")
def warn(msg):  print(f"  {YELLOW}⚠{RESET} {msg}")
def header(msg): print(f"\n{BOLD}{msg}{RESET}")


async def check_usda_ams():
    header("USDA AMS Market News  (LM_GR212 — CA Direct Hay)")
    if not USDA_AMS_KEY:
        warn("USDA_AMS_API_KEY not set — skipping")
        return False

    url = "https://marsapi.ams.usda.gov/services/v1.2/reports/LM_GR212"
    headers = {"Authorization": f"Bearer {USDA_AMS_KEY}"}
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url, headers=headers, params={"allSections": "true"})
        if r.status_code == 200:
            data = r.json()
            count = len(data) if isinstance(data, list) else len(data.get("results", []))
            ok(f"Connected — {count} records in latest report")
            return True
        elif r.status_code == 401:
            fail(f"401 Unauthorized — check your USDA_AMS_API_KEY")
        elif r.status_code == 404:
            warn("404 — report slug LM_GR212 may have changed; data pipeline will adapt")
        else:
            fail(f"HTTP {r.status_code}: {r.text[:120]}")
    except Exception as e:
        fail(f"Connection error: {e}")
    return False


async def check_usda_nass():
    header("USDA NASS Quick Stats  (CA hay production)")
    if not USDA_NASS_KEY:
        warn("USDA_NASS_API_KEY not set — skipping")
        return False

    url = "https://quickstats.nass.usda.gov/api/api/GET"
    params = {
        "key": USDA_NASS_KEY,
        "source_desc": "SURVEY",
        "commodity_desc": "HAY",
        "state_name": "CALIFORNIA",
        "year": "2023",
        "format": "JSON",
    }
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            count = len(data.get("data", []))
            if count:
                ok(f"Connected — {count} records returned for CA hay 2023")
                return True
            else:
                warn("Connected but 0 records — key may be valid, data just sparse")
                return True
        elif r.status_code == 401 or "unauthorized" in r.text.lower():
            fail("Unauthorized — check your USDA_NASS_API_KEY")
        else:
            fail(f"HTTP {r.status_code}: {r.text[:120]}")
    except Exception as e:
        fail(f"Connection error: {e}")
    return False


async def check_noaa():
    header("NOAA Climate Data Online  (weather stations)")
    if not NOAA_KEY:
        warn("NOAA_API_KEY not set — skipping")
        return False

    url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/stations/GHCND:USW00023232"
    headers = {"token": NOAA_KEY}
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            name = data.get("name", "unknown station")
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

    url = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"
    params = {
        "api_key": EIA_KEY,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[product][]": "EPD2DXL0",
        "facets[area][]": "CA",
        "length": 1,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            records = data.get("response", {}).get("data", [])
            if records:
                latest = records[0]
                ok(f"Connected — latest CA diesel: ${latest.get('value', '?')}/gal ({latest.get('period', '?')})")
            else:
                warn("Connected but no records returned — key may still be valid")
            return True
        elif r.status_code == 403 or "invalid" in r.text.lower():
            fail("403 / Invalid API key — check your EIA_API_KEY")
        else:
            fail(f"HTTP {r.status_code}: {r.text[:120]}")
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

    passed = sum(1 for r in results if r)
    skipped = sum(1 for k in [USDA_AMS_KEY, USDA_NASS_KEY, NOAA_KEY, EIA_KEY] if not k)

    print(f"\n{BOLD}{'='*50}{RESET}")
    print(f"  {GREEN}{passed} passed{RESET}  |  {YELLOW}{skipped} skipped (no key){RESET}  |  {RED}{4 - passed - skipped} failed{RESET}")
    print()

    if passed == 4:
        print(f"  {GREEN}{BOLD}All APIs ready! Trigger live ingestion:{RESET}")
        print("  curl -X POST http://localhost:8000/api/v1/ingestion/trigger/usda_ams")
        print("  curl -X POST http://localhost:8000/api/v1/ingestion/trigger/eia")
        print("  curl -X POST http://localhost:8000/api/v1/ingestion/trigger/drought_monitor")
        print("  curl -X POST http://localhost:8000/api/v1/ingestion/trigger/noaa")
    elif skipped > 0:
        print(f"  {YELLOW}Add missing keys to .env then re-run this script.{RESET}")
    else:
        print(f"  {RED}Fix the failing keys in .env then re-run.{RESET}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
