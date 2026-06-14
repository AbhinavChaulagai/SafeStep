"""
NYC Crime ingestion — pulls from NYC Open Data (NYPD complaint dataset).
Endpoint: https://data.cityofnewyork.us/resource/qgea-i56i.json

Usage:
  python -m ingestion.nyc_crime            # historical (2 years)
  python -m ingestion.nyc_crime --incremental  # last 24 hours only
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import date, timedelta
from sodapy import Socrata
from sqlalchemy import text

sys.path.insert(0, ".")
from config import settings
from database import AsyncSessionLocal, init_db

log = logging.getLogger(__name__)

SOCRATA_DOMAIN = "data.cityofnewyork.us"
DATASET_ID = "qgea-i56i"
CHUNK_SIZE = 10_000  # records per Socrata API call

OFFENSE_CATEGORY_MAP: dict[str, str] = {
    "FELONY ASSAULT": "violent",
    "ROBBERY": "violent",
    "RAPE": "violent",
    "MURDER & NON-NEGL. MANSLAUGHTER": "violent",
    "KIDNAPPING & RELATED OFFENSES": "violent",
    "HOMICIDE-NEGLIGENT-VEHICLE": "violent",
    "GRAND LARCENY": "theft",
    "PETIT LARCENY": "theft",
    "GRAND LARCENY OF MOTOR VEHICLE": "theft",
    "THEFT-FRAUD": "theft",
    "THEFT OF SERVICES": "theft",
    "BURGLARY": "property",
    "CRIMINAL MISCHIEF & RELATED OF": "property",
    "ARSON": "property",
    "CRIMINAL TRESPASS": "property",
    "POSSESSION OF STOLEN PROPERTY": "property",
}

# Batch INSERT with PostGIS spatial join to assign neighborhood_id.
# Uses json_to_recordset so the entire batch is one round-trip to PostgreSQL.
BATCH_INSERT_SQL = text("""
    WITH batch AS (
        SELECT * FROM json_to_recordset(:data) AS x(
            external_id      text,
            offense_category text,
            offense_desc     text,
            inc_date         text,
            inc_time         text,
            time_bucket      text,
            lat              float8,
            lng              float8
        )
    )
    INSERT INTO crime_incidents
        (neighborhood_id, city, offense_category, offense_description,
         incident_date, incident_time, time_bucket, lat, lng, source, external_id)
    SELECT
        n.id,
        'nyc',
        b.offense_category,
        b.offense_desc,
        b.inc_date::date,
        b.inc_time::time,
        b.time_bucket,
        b.lat,
        b.lng,
        'nypd',
        b.external_id
    FROM batch b
    LEFT JOIN LATERAL (
        SELECT id FROM neighborhoods
        WHERE ST_Within(
            ST_SetSRID(ST_MakePoint(b.lng, b.lat), 4326),
            geom
        )
        LIMIT 1
    ) n ON true
    WHERE b.external_id IS NOT NULL AND b.external_id <> ''
    ON CONFLICT (external_id) DO NOTHING
""")


# ── helpers ──────────────────────────────────────────────────────────────────

def categorize(desc: str) -> str:
    return OFFENSE_CATEGORY_MAP.get(desc.upper().strip(), "other")


def time_bucket(time_str: str) -> str:
    try:
        hour = int((time_str or "")[:2])
    except (ValueError, IndexError):
        return "evening"
    if 6 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "afternoon"
    if 18 <= hour < 23:
        return "evening"
    return "late_night"


def transform(row: dict) -> dict | None:
    try:
        lat = float(row.get("latitude") or 0)
        lng = float(row.get("longitude") or 0)
    except (ValueError, TypeError):
        return None
    if not lat or not lng:
        return None

    desc = (row.get("ofns_desc") or "").strip()
    t = (row.get("cmplnt_fr_tm") or "")[:8] or None  # "HH:MM:SS" or None
    d = (row.get("cmplnt_fr_dt") or "")[:10] or None  # "YYYY-MM-DD" or None

    return {
        "external_id": row.get("cmplnt_num", ""),
        "offense_category": categorize(desc),
        "offense_desc": desc[:255],
        "inc_date": d,
        "inc_time": t,
        "time_bucket": time_bucket(row.get("cmplnt_fr_tm") or ""),
        "lat": lat,
        "lng": lng,
    }


# ── core ─────────────────────────────────────────────────────────────────────

def _fetch_chunk(client: Socrata, since: str, offset: int) -> list[dict]:
    return client.get(
        DATASET_ID,
        where=(
            f"cmplnt_fr_dt >= '{since}T00:00:00.000' "
            f"AND latitude IS NOT NULL AND longitude IS NOT NULL"
        ),
        select="cmplnt_num,ofns_desc,law_cat_cd,cmplnt_fr_dt,cmplnt_fr_tm,latitude,longitude",
        limit=CHUNK_SIZE,
        offset=offset,
    )


async def _insert_batch(db, records: list[dict]) -> int:
    if not records:
        return 0
    result = await db.execute(BATCH_INSERT_SQL, {"data": json.dumps(records)})
    await db.commit()
    # rowcount may be -1 with some drivers; treat negative as 0
    return max(result.rowcount, 0)


async def ingest(db, incremental: bool = True) -> int:
    days_back = 1 if incremental else 730  # 2 years
    since = (date.today() - timedelta(days=days_back)).isoformat()

    client = Socrata(
        SOCRATA_DOMAIN,
        settings.socrata_app_token or None,
        timeout=120,
    )

    total = 0
    offset = 0
    page = 0

    log.info("NYC crime ingest started (incremental=%s, since=%s)", incremental, since)

    while True:
        page += 1
        log.info("  Page %d  offset=%d", page, offset)
        rows = _fetch_chunk(client, since, offset)
        if not rows:
            break

        records = [r for row in rows if (r := transform(row))]
        inserted = await _insert_batch(db, records)
        total += inserted
        log.info("    fetched=%d  valid=%d  new=%d  total=%d", len(rows), len(records), inserted, total)

        if len(rows) < CHUNK_SIZE:
            break
        offset += CHUNK_SIZE

    log.info("NYC crime ingest complete. Total new records: %d", total)
    return total


# ── entrypoint ────────────────────────────────────────────────────────────────

async def _main():
    incremental = "--incremental" in sys.argv
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
    )
    await init_db()
    async with AsyncSessionLocal() as db:
        count = await ingest(db, incremental=incremental)
    print(f"\nFinished. {count} new records inserted.")


if __name__ == "__main__":
    asyncio.run(_main())
