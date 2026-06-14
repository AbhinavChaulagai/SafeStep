"""
Loads NYC NTA (Neighborhood Tabulation Areas) boundaries into the neighborhoods table.
Run this before crime ingestion so the spatial join has data to match against.

Uses sodapy to fetch NTA data (geometry in 'the_geom' field).
Dataset: 2020 NTA boundaries — https://data.cityofnewyork.us/resource/9nt8-h7nd
"""

import asyncio
import json
import sys

sys.path.insert(0, ".")

from sodapy import Socrata
from sqlalchemy import text

from config import settings
from database import AsyncSessionLocal, init_db

SOCRATA_DOMAIN = "data.cityofnewyork.us"
NTA_DATASET_ID = "9nt8-h7nd"   # 2020 Neighborhood Tabulation Areas


def _build_client() -> Socrata:
    return Socrata(SOCRATA_DOMAIN, settings.socrata_app_token or None, timeout=60)


def _fetch_all_ntas() -> list[dict]:
    client = _build_client()
    # NTA dataset has ~263 rows; fetch all at once
    return client.get(NTA_DATASET_ID, limit=500, select="ntaname,boroname,the_geom")


def _to_multipolygon(geom: dict) -> dict:
    """Ensure geometry is MultiPolygon."""
    if geom["type"] == "Polygon":
        return {"type": "MultiPolygon", "coordinates": [geom["coordinates"]]}
    return geom


async def load_neighborhoods(db) -> int:
    print("Fetching NYC NTA boundaries via Socrata API...")
    rows = _fetch_all_ntas()
    print(f"  Received {len(rows)} NTA features")

    count = 0
    for row in rows:
        geom_raw = row.get("the_geom")
        if not geom_raw:
            continue

        name = (row.get("ntaname") or "").strip()
        borough = (row.get("boroname") or "").strip()
        if not name:
            continue

        geom = _to_multipolygon(geom_raw)

        await db.execute(
            text("""
                INSERT INTO neighborhoods (name, city, borough, geom)
                VALUES (
                    :name,
                    'nyc',
                    :borough,
                    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326))
                )
                ON CONFLICT DO NOTHING
            """),
            {"name": name, "borough": borough, "geom": json.dumps(geom)},
        )
        count += 1

    await db.commit()
    return count


async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT COUNT(*) FROM neighborhoods WHERE city = 'nyc'")
        )
        existing = result.scalar()
        if existing and existing > 0:
            print(f"Neighborhoods already loaded ({existing} rows). Skipping.")
            return

        count = await load_neighborhoods(db)
        print(f"\nDone. Loaded {count} NYC neighborhoods.")

        result = await db.execute(
            text("SELECT name, borough FROM neighborhoods WHERE city = 'nyc' ORDER BY borough, name LIMIT 8")
        )
        rows = result.fetchall()
        print("\nSample neighborhoods:")
        for r in rows:
            print(f"  {r.name} ({r.borough})")


if __name__ == "__main__":
    asyncio.run(main())
