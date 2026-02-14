"""
External API client for nonprofit intelligence data sources.

Wraps ProPublica Nonprofits API and USAspending API with
timeout handling and graceful error recovery.
"""

import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

PROPUBLICA_BASE = "https://projects.propublica.org/nonprofits/api/v2"
USASPENDING_BASE = "https://api.usaspending.gov/api/v2"

REQUEST_TIMEOUT = 15.0  # seconds


def clean_ein(ein: str) -> str:
    """Strip non-digit characters and return normalized EIN."""
    return re.sub(r"[^0-9]", "", ein)


def normalize_name(name: str) -> str:
    """Lowercase and strip special characters for fuzzy matching."""
    return re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()


def to_float_or_none(val) -> Optional[float]:
    """Safely convert to float or return None."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


async def propublica_search(query: str) -> dict:
    """
    Search ProPublica Nonprofits API by name or EIN.

    Returns raw API response dict or empty dict on failure.
    """
    url = f"{PROPUBLICA_BASE}/search.json"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(url, params={"q": query})
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning(f"ProPublica search failed for '{query}': {e}")
        return {}


async def propublica_org(ein: str) -> dict:
    """
    Fetch full organization detail from ProPublica by EIN.

    Returns the full response including organization, filings_with_data, and officers.
    """
    normalized = clean_ein(ein)
    url = f"{PROPUBLICA_BASE}/organizations/{normalized}.json"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning(f"ProPublica org fetch failed for EIN {normalized}: {e}")
        return {}


async def usaspending_awards(
    ein: str,
    from_date: str = "2019-01-01",
    to_date: str = "2030-01-01",
) -> dict:
    """
    Fetch federal awards from USAspending API by recipient EIN.

    Returns raw API response dict or empty dict on failure.
    """
    normalized = clean_ein(ein)
    url = f"{USASPENDING_BASE}/search/spending_by_award/"
    body = {
        "filters": {
            "recipient_search_text": [normalized],
            "time_period": [{"start_date": from_date, "end_date": to_date}],
        },
        "fields": [
            "Award ID",
            "Recipient Name",
            "Action Date",
            "Award Amount",
            "Awarding Agency",
            "Award Type",
            "Description",
            "Recipient City Name",
            "Recipient State Code",
        ],
        "page": 1,
        "limit": 100,
        "sort": "Action Date",
        "order": "desc",
        "subawards": False,
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning(f"USAspending awards fetch failed for EIN {normalized}: {e}")
        return {}
