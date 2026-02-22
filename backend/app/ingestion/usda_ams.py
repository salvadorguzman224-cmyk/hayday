"""
USDA AMS Market News API client.

Pulls the California Direct Hay Report (slug: LM_GR212) and transforms
the JSON payload into HayPrice records.

API docs: https://marsapi.ams.usda.gov/services/v1.2/
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://marsapi.ams.usda.gov/services/v1.2"
REPORT_SLUG = "LM_GR212"  # California Direct Hay — Weekly

# Map USDA region strings to internal keys
REGION_MAP: dict[str, str] = {
    "Northern California": "northern_ca",
    "Northern CA": "northern_ca",
    "Sacramento Valley": "sacramento_valley",
    "Central California": "san_joaquin_valley",
    "San Joaquin Valley": "san_joaquin_valley",
    "Southern California": "southern_ca",
    "Desert": "southern_ca",
    "Imperial Valley": "southern_ca",
    "Coastal": "coastal_ca",
}

HAY_TYPE_MAP: dict[str, str] = {
    "Alfalfa": "alfalfa",
    "Grass": "grass",
    "Oat": "oat",
    "Oat Hay": "oat",
    "Sudan": "sudan",
    "Sudan Grass": "sudan",
    "Mixed": "mixed",
    "Straw": "straw",
}

GRADE_MAP: dict[str, str] = {
    "Supreme": "supreme",
    "Premium": "premium",
    "Good": "good",
    "Fair": "fair",
    "Utility": "utility",
}


class USDAamsClient:
    def __init__(self) -> None:
        self._api_key = settings.USDA_AMS_API_KEY
        # MARS API uses HTTP Basic Auth: api_key as username, empty password
        self._auth = (self._api_key, "") if self._api_key else None

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=2, max=30))
    async def fetch_latest(self) -> list[dict[str, Any]]:
        """Fetch the most recent California Direct Hay Report."""
        url = f"{BASE_URL}/reports/{REPORT_SLUG}"
        params = {"allSections": "true"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, auth=self._auth, params=params)
            resp.raise_for_status()
            data = resp.json()

        return self._parse(data)

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=2, max=30))
    async def fetch_for_date(self, report_date: date) -> list[dict[str, Any]]:
        """Fetch report for a specific date (YYYY-MM-DD)."""
        url = f"{BASE_URL}/reports/{REPORT_SLUG}/{report_date.isoformat()}"
        params = {"allSections": "true"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, auth=self._auth, params=params)
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            data = resp.json()

        return self._parse(data)

    def _parse(self, raw: Any) -> list[dict[str, Any]]:
        """
        Parse USDA AMS JSON response into a list of normalized price records.
        The USDA API returns a list of report entries; each entry has commodity,
        class, grade, price fields, etc.
        """
        records: list[dict[str, Any]] = []

        # The response can be a list or wrapped in a dict
        entries = raw if isinstance(raw, list) else raw.get("results", [])

        for entry in entries:
            try:
                region_raw = (
                    entry.get("office_city")
                    or entry.get("reporting_area")
                    or entry.get("region")
                    or ""
                )
                region = self._map_region(region_raw)
                if not region:
                    continue

                commodity = entry.get("commodity_name", entry.get("commodity", ""))
                hay_type = self._map_hay_type(commodity)
                if not hay_type:
                    continue

                grade_raw = entry.get("class", entry.get("grade", ""))
                grade = GRADE_MAP.get(grade_raw.strip().title())

                try:
                    price_low = float(entry["price_min"]) if entry.get("price_min") else None
                    price_high = float(entry["price_max"]) if entry.get("price_max") else None
                    price_wtavg = float(
                        entry.get("wtavg_price")
                        or entry.get("price_wtavg")
                        or ((price_low or 0) + (price_high or 0)) / 2
                    )
                except (TypeError, ValueError):
                    continue

                report_date_raw = entry.get("report_date") or entry.get("week_ending_date")
                try:
                    report_date = datetime.strptime(report_date_raw, "%m/%d/%Y").date()
                except (TypeError, ValueError):
                    try:
                        report_date = datetime.fromisoformat(report_date_raw).date()
                    except (TypeError, ValueError):
                        report_date = date.today()

                volume_raw = entry.get("volume") or entry.get("total_volume")
                try:
                    volume = int(float(volume_raw)) if volume_raw else None
                except (TypeError, ValueError):
                    volume = None

                delivery = entry.get("transaction_type", "fob").lower()
                delivery = "fob" if "fob" in delivery else "delivered"

                records.append(
                    {
                        "report_date": report_date,
                        "source": "usda_ams",
                        "region": region,
                        "hay_type": hay_type,
                        "grade": grade,
                        "price_low": price_low,
                        "price_high": price_high,
                        "price_wtavg": round(price_wtavg, 2),
                        "volume_tons": volume,
                        "delivery_type": delivery,
                    }
                )
            except Exception as exc:
                logger.warning("Skipping USDA AMS entry due to parse error: %s", exc)
                continue

        logger.info("USDA AMS: parsed %d records", len(records))
        return records

    @staticmethod
    def _map_region(raw: str) -> str | None:
        for key, val in REGION_MAP.items():
            if key.lower() in raw.lower():
                return val
        return None

    @staticmethod
    def _map_hay_type(raw: str) -> str | None:
        for key, val in HAY_TYPE_MAP.items():
            if key.lower() in raw.lower():
                return val
        return None
