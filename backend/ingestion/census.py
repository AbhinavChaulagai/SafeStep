"""
Census ACS ingestion — pulls demographic data for NYC neighborhoods.
Used for context calibration only, never for scoring.
"""

import httpx
from config import settings

ACS_BASE = "https://api.census.gov/data/2022/acs/acs5"

# ACS variable codes
VARS = {
    "B01003_001E": "population",
    "B19013_001E": "median_income",
    "B01002_001E": "median_age",
}


async def fetch_nyc_tracts() -> list[dict]:
    if not settings.census_api_key:
        return []
    variables = ",".join(VARS.keys())
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            ACS_BASE,
            params={
                "get": variables,
                "for": "tract:*",
                "in": "state:36 county:061,047,081,005,085",  # NYC counties
                "key": settings.census_api_key,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    headers = data[0]
    return [dict(zip(headers, row)) for row in data[1:]]


async def ingest(db) -> int:
    """Pull ACS data, aggregate to neighborhoods via spatial join, upsert demographic_context."""
    # TODO: implement spatial aggregation
    return 0
