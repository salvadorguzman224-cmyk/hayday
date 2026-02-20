"""
U.S. Drought Monitor API client.

Fetches weekly drought severity statistics for California counties/regions.
API: https://droughtmonitor.unl.edu/api/ (no auth required)
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

BASE_URL = "https://droughtmonitor.unl.edu/api/webservice"

# Map our internal regions to CA county lists for the Drought Monitor query
REGION_COUNTIES: dict[str, list[str]] = {
    "northern_ca": ["Shasta", "Lassen", "Modoc", "Siskiyou", "Trinity"],
    "sacramento_valley": ["Sacramento", "Yolo", "Glenn", "Colusa", "Butte"],
    "san_joaquin_valley": ["Fresno", "Tulare", "Kern", "Kings", "Merced"],
    "southern_ca": ["Imperial", "Riverside", "San Bernardino"],
    "coastal_ca": ["Marin", "Sonoma", "Santa Barbara", "Monterey"],
}


class DroughtMonitorClient:
    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=2, max=30))
    async def fetch_for_date(self, report_date: date) -> list[dict[str, Any]]:
        """Fetch drought statistics for all CA regions on the given report date."""
        records: list[dict[str, Any]] = []

        date_str = report_date.strftime("%Y%m%d")

        # Single state-level request for California
        url = f"{BASE_URL}/comprehensivestats/"
        params = {
            "aoi": "state",
            "aoitext": "California",
            "date": date_str,
            "statisticsType": "1",  # % area
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                logger.warning("Drought Monitor fetch error: %s", exc)
                return []

        state_record = self._parse_state(data, report_date)
        if state_record:
            # Broadcast the state-level numbers to all regions
            for region in REGION_COUNTIES:
                records.append({**state_record, "region": region})

        logger.info("Drought Monitor: parsed %d records for %s", len(records), report_date)
        return records

    def _parse_state(self, data: Any, report_date: date) -> dict[str, Any] | None:
        try:
            if isinstance(data, list):
                entry = data[0] if data else {}
            else:
                entry = data

            return {
                "report_date": report_date,
                "region": "california",  # will be overridden per-region
                "d0_pct": float(entry.get("D0", 0) or 0),
                "d1_pct": float(entry.get("D1", 0) or 0),
                "d2_pct": float(entry.get("D2", 0) or 0),
                "d3_pct": float(entry.get("D3", 0) or 0),
                "d4_pct": float(entry.get("D4", 0) or 0),
            }
        except Exception as exc:
            logger.warning("Drought Monitor parse error: %s", exc)
            return None
