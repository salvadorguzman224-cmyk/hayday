"""
USDA NASS Quick Stats API client.

Fetches California hay production, stocks, and crop progress data.
API: https://quickstats.nass.usda.gov/api/
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://quickstats.nass.usda.gov"


class USDANassClient:
    def __init__(self) -> None:
        self._api_key = settings.USDA_NASS_API_KEY

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=2, max=30))
    async def fetch_production(self, year: int) -> list[dict[str, Any]]:
        """Fetch CA hay production data for a given year."""
        if not self._api_key:
            logger.info("USDA NASS API key not configured — skipping")
            return []

        params = {
            "key": self._api_key,
            "source_desc": "SURVEY",
            "sector_desc": "CROPS",
            "commodity_desc": "HAY",
            "statisticcat_desc": "PRODUCTION",
            "state_name": "CALIFORNIA",
            "year": str(year),
            "format": "JSON",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{BASE_URL}/api/GET", params=params)
            resp.raise_for_status()
            data = resp.json()

        return self._parse_production(data.get("data", []))

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=2, max=30))
    async def fetch_stocks(self, year: int) -> list[dict[str, Any]]:
        """Fetch CA hay stocks data for a given year."""
        if not self._api_key:
            return []

        params = {
            "key": self._api_key,
            "source_desc": "SURVEY",
            "sector_desc": "CROPS",
            "commodity_desc": "HAY",
            "statisticcat_desc": "STOCKS",
            "state_name": "CALIFORNIA",
            "year": str(year),
            "format": "JSON",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{BASE_URL}/api/GET", params=params)
            resp.raise_for_status()
            data = resp.json()

        return self._parse_production(data.get("data", []))

    def _parse_production(self, entries: list[dict]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for entry in entries:
            try:
                value_str = entry.get("Value", "").replace(",", "")
                if not value_str or value_str == " (D)" or value_str == "(NA)":
                    continue

                year = int(entry.get("year", 0))
                # NASS data is typically annual — use Jan 1 as the date
                month = int(entry.get("reference_period_desc", "Jan").split(" ")[0][:2]
                            if entry.get("reference_period_desc", "").startswith(
                                ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
                            ) else 1)
                report_date = date(year, 1, 1)

                commodity = entry.get("commodity_desc", "hay").lower()
                unit = entry.get("unit_desc", "TONS")

                records.append(
                    {
                        "report_date": report_date,
                        "region": "california",
                        "hay_type": commodity if commodity in ["alfalfa", "grass"] else "mixed",
                        "value": float(value_str),
                        "unit": unit,
                        "source": "usda_nass",
                    }
                )
            except Exception as exc:
                logger.warning("NASS parse error: %s", exc)
                continue

        logger.info("USDA NASS: parsed %d production records", len(records))
        return records
