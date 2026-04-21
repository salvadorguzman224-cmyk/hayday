"""
NOAA Climate Data Online API client.

Fetches precipitation and temperature data for California stations.
API: https://www.ncdc.noaa.gov/cdo-web/api/v2/
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2"

# Representative NOAA GHCND stations per CA region (approximate — one station
# per region; tune if a specific hay-growing area is under-represented).
REGION_STATIONS: dict[str, str] = {
    "central_san_joaquin_valley": "GHCND:USW00093193",  # Fresno Air Terminal
    "north_intermountain":        "GHCND:USW00024216",  # Alturas (Modoc)
    "north_san_joaquin_valley":   "GHCND:USW00023258",  # Modesto
    "sacramento_valley":          "GHCND:USW00023232",  # Sacramento Executive
    "southeast":                  "GHCND:USW00003144",  # El Centro / Imperial
}


class NOAAClient:
    def __init__(self) -> None:
        self._api_key = settings.NOAA_API_KEY

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=2, max=30))
    async def fetch_weather(
        self, region: str, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """Fetch daily precipitation and temperature for a region and date range."""
        if not self._api_key:
            logger.info("NOAA API key not configured — skipping")
            return []

        station = REGION_STATIONS.get(region)
        if not station:
            return []

        headers = {"token": self._api_key}
        params = {
            "datasetid": "GHCND",
            "stationid": station,
            "startdate": start_date.isoformat(),
            "enddate": end_date.isoformat(),
            "datatypeid": "PRCP,TMAX,TMIN",
            "limit": 1000,
            "units": "metric",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{BASE_URL}/data", headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        return self._parse(data.get("results", []), region, station)

    def _parse(self, entries: list[dict], region: str, station_id: str) -> list[dict[str, Any]]:
        from collections import defaultdict

        # Group by date
        by_date: dict[str, dict] = defaultdict(lambda: {"prcp": None, "tmax": None, "tmin": None})
        for entry in entries:
            obs_date = entry.get("date", "")[:10]
            dtype = entry.get("datatype")
            value = entry.get("value")
            if dtype == "PRCP":
                by_date[obs_date]["prcp"] = value / 10.0 if value is not None else None  # tenths of mm → mm
            elif dtype == "TMAX":
                by_date[obs_date]["tmax"] = value / 10.0 if value is not None else None  # tenths of °C
            elif dtype == "TMIN":
                by_date[obs_date]["tmin"] = value / 10.0 if value is not None else None

        records = [
            {
                "observation_date": date.fromisoformat(d),
                "station_id": station_id,
                "region": region,
                "precipitation_mm": v["prcp"],
                "temp_max_c": v["tmax"],
                "temp_min_c": v["tmin"],
            }
            for d, v in sorted(by_date.items())
        ]

        logger.info("NOAA: parsed %d weather records for %s", len(records), region)
        return records
