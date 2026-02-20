"""
EIA Open Data API client.

Fetches weekly on-highway diesel fuel prices for California.
API: https://api.eia.gov/v2/
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.eia.gov/v2"


class EIAClient:
    def __init__(self) -> None:
        self._api_key = settings.EIA_API_KEY

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=2, max=30))
    async def fetch_diesel_prices(
        self, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """Fetch weekly CA on-highway diesel prices ($/gallon)."""
        if not self._api_key:
            logger.info("EIA API key not configured — skipping")
            return []

        params = {
            "api_key": self._api_key,
            "frequency": "weekly",
            "data[0]": "value",
            "facets[product][]": "EPD2DXL0",  # on-highway diesel
            "facets[area][]": "CA",            # California
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "length": 5000,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{BASE_URL}/petroleum/pri/gnd/data/", params=params
            )
            resp.raise_for_status()
            data = resp.json()

        return self._parse(data.get("response", {}).get("data", []))

    def _parse(self, entries: list[dict]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for entry in entries:
            try:
                period = entry.get("period", "")
                report_date = date.fromisoformat(period) if period else None
                if not report_date:
                    continue

                value = entry.get("value")
                if value is None:
                    continue

                records.append(
                    {
                        "report_date": report_date,
                        "region": "california",
                        "price_per_gallon": round(float(value), 3),
                    }
                )
            except Exception as exc:
                logger.warning("EIA parse error: %s", exc)
                continue

        logger.info("EIA: parsed %d diesel price records", len(records))
        return records
