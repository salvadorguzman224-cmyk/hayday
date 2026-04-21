"""
USDA AMS Market News API client.

The California Direct Hay Report (slug 2904) does NOT return structured price
fields. Each entry contains a `report_narrative` prose block — we parse prices,
demand signals, and trade activity out of that text.

Pre-Aug 2020 entries use the legacy slug `ML_GR311` with a
`market_location_name == 'Non Mars Location'` placeholder and null narratives;
those are skipped.

API docs: https://marsapi.ams.usda.gov/services/v1.2/
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://marsapi.ams.usda.gov/services/v1.2"
REPORT_SLUG = "2904"  # California Direct Hay Report (weekly)
OFFICE_REGION = "san_joaquin_valley"  # Moses Lake-less, CA-wide report; default bucket

HAY_TYPE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\balfalfa\b", re.I), "alfalfa"),
    (re.compile(r"\bsudan(?:\s*grass)?\b", re.I), "sudan"),
    (re.compile(r"\boat(?:\s*hay)?\b", re.I), "oat"),
    (re.compile(r"\bwheat\s*(?:hay|straw)?\b", re.I), "wheat"),
    (re.compile(r"\brice\s*straw\b", re.I), "straw"),
    (re.compile(r"\bstraw\b", re.I), "straw"),
    (re.compile(r"\bbermuda\b", re.I), "grass"),
    (re.compile(r"\b(?:forage\s*)?mix(?:ed)?\b", re.I), "mixed"),
    (re.compile(r"\bklein\s*grass\b", re.I), "grass"),
    (re.compile(r"\btimothy\b", re.I), "grass"),
    (re.compile(r"\bgrass\s*hay\b", re.I), "grass"),
]

GRADE_KEYWORDS: dict[str, str] = {
    "supreme": "supreme",
    "premium": "premium",
    "good": "good",
    "fair": "fair",
    "utility": "utility",
}

# Price line: grade + hay type + price range, e.g.
#   "Supreme Alfalfa: 320.00-350.00"
#   "Premium/Supreme Alfalfa 275-300 Delivered"
#   "Good Alfalfa 210.00 - 235.00 FOB"
PRICE_LINE_RE = re.compile(
    r"""
    (?P<grade>supreme|premium|good|fair|utility)
    (?:\s*/\s*(?:supreme|premium|good|fair|utility))?   # optional compound grade
    \s+
    (?P<commodity>alfalfa|sudan(?:\s*grass)?|oat(?:\s*hay)?|wheat\s*(?:hay|straw)?|
                  rice\s*straw|straw|bermuda|timothy|klein\s*grass|grass\s*hay|mix(?:ed)?)
    [\s:,-]*
    (?P<low>\d{2,4}(?:\.\d{1,2})?)
    \s*(?:-|to|–)\s*
    (?P<high>\d{2,4}(?:\.\d{1,2})?)
    (?:\s*(?P<delivery>delivered|fob|f\.o\.b\.|picked\s*up))?
    """,
    re.I | re.X,
)

DEMAND_RE = re.compile(
    r"(retail(?:/stable)?|stable|dairy|export)[^.]*?"
    r"(very\s+light|light(?:\s+to\s+moderate)?|moderate(?:\s+to\s+good)?|good|strong)\s+demand",
    re.I,
)


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
        """Fetch report(s) for a specific date (YYYY-MM-DD)."""
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
        Parse AMS JSON (a list of report envelopes) into HayPrice rows.
        Each envelope's `report_narrative` is scanned for (grade, hay_type, price range)
        tuples. Envelopes with null narratives or 'Non Mars Location' placeholders
        (pre-Aug 2020 legacy slug) are skipped.
        """
        records: list[dict[str, Any]] = []
        entries = raw if isinstance(raw, list) else raw.get("results", [])

        for entry in entries:
            try:
                if entry.get("market_location_name") == "Non Mars Location":
                    continue

                narrative = entry.get("report_narrative")
                if not narrative:
                    continue

                report_date = self._parse_report_date(entry)
                if report_date is None:
                    continue

                narrative_clean = self._clean_narrative(narrative)
                price_rows = self._extract_prices(narrative_clean, report_date)
                records.extend(price_rows)

            except Exception as exc:
                logger.warning("Skipping USDA AMS entry due to parse error: %s", exc)
                continue

        logger.info("USDA AMS: parsed %d price records from narrative", len(records))
        return records

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _parse_report_date(entry: dict[str, Any]) -> date | None:
        raw = entry.get("report_date") or entry.get("published_date") or entry.get("report_end_date")
        if not raw:
            return None
        # AMS serves ISO 8601 ("2024-09-13T00:00:00") and occasionally MM/DD/YYYY
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(raw[: len(fmt) + 4], fmt).date()
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clean_narrative(text: str) -> str:
        # Collapse HTML breaks, non-breaking spaces, and whitespace runs
        cleaned = re.sub(r"<[^>]+>", " ", text)
        cleaned = cleaned.replace("\xa0", " ").replace("\r", " ")
        return re.sub(r"\s+", " ", cleaned).strip()

    def _extract_prices(
        self, narrative: str, report_date: date
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()

        for m in PRICE_LINE_RE.finditer(narrative):
            grade = GRADE_KEYWORDS.get(m.group("grade").lower())
            hay_type = self._map_hay_type(m.group("commodity"))
            if not grade or not hay_type:
                continue

            try:
                low = float(m.group("low"))
                high = float(m.group("high"))
            except (TypeError, ValueError):
                continue
            if low <= 0 or high <= 0 or high < low or high > 2000:
                continue

            delivery_raw = (m.group("delivery") or "").lower()
            delivery = "fob" if "fob" in delivery_raw or "picked" in delivery_raw else (
                "delivered" if "deliver" in delivery_raw else None
            )

            # Dedupe by (hay_type, grade, delivery): keep first occurrence per report
            key = (hay_type, grade, delivery or "unknown")
            if key in seen:
                continue
            seen.add(key)

            rows.append(
                {
                    "report_date": report_date,
                    "source": "usda_ams",
                    "region": OFFICE_REGION,
                    "hay_type": hay_type,
                    "grade": grade,
                    "price_low": low,
                    "price_high": high,
                    "price_wtavg": round((low + high) / 2, 2),
                    "volume_tons": None,
                    "delivery_type": delivery or "fob",
                }
            )

        return rows

    @staticmethod
    def _map_hay_type(raw: str) -> str | None:
        for pattern, val in HAY_TYPE_PATTERNS:
            if pattern.search(raw):
                return val
        return None

    @staticmethod
    def extract_demand_signals(narrative: str) -> dict[str, str]:
        """Utility for downstream features: pulls {segment: level} from prose."""
        signals: dict[str, str] = {}
        for m in DEMAND_RE.finditer(narrative):
            segment = m.group(1).lower().split("/")[0]
            segment = "retail" if segment == "stable" else segment
            signals.setdefault(segment, m.group(2).lower().strip())
        return signals
