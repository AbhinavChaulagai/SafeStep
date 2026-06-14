"""
Scoring service — computes neighborhood_scores from crime_incidents.

Formula (per spec):
  weighted = violent_rate * 3.0 + theft_rate * 1.5 + property_rate * 1.0
  composite = weighted * time_multiplier
  Normalized to 0–100 using the 95th-percentile of composite_raw as the ceiling.
  Risk bands: 0–25 Low | 26–50 Moderate | 51–75 Elevated | 76–100 High
"""
from __future__ import annotations

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

TIME_MULTIPLIERS = {
    "morning": 0.8,
    "afternoon": 0.9,
    "evening": 1.2,
    "late_night": 1.4,
}

RISK_BANDS = [
    (0,  25,  "Low"),
    (26, 50,  "Moderate"),
    (51, 75,  "Elevated"),
    (76, 100, "High"),
]


def score_to_band(score: float) -> str:
    for low, high, band in RISK_BANDS:
        if low <= score <= high:
            return band
    return "High"


async def calculate_risk_band(
    neighborhood_id: int, time_bucket: str, db: AsyncSession
) -> dict:
    """Return current score + band for one neighborhood × time_bucket pair."""
    from models.crime import NeighborhoodScore
    from sqlalchemy import select

    result = await db.execute(
        select(NeighborhoodScore).where(
            NeighborhoodScore.neighborhood_id == neighborhood_id,
            NeighborhoodScore.time_bucket == time_bucket,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return {"composite_score": 0.0, "risk_band": "Low", "yoy_trend": 0.0}

    return {
        "composite_score": row.composite_score or 0.0,
        "risk_band": row.risk_band or "Low",
        "yoy_trend": row.yoy_trend or 0.0,
    }


# ── full nightly recomputation ─────────────────────────────────────────────

_RECOMPUTE_SQL = text("""
WITH
-- 1-year incident counts per (neighborhood, time_bucket)
recent_counts AS (
    SELECT
        neighborhood_id,
        time_bucket,
        COUNT(*) FILTER (WHERE offense_category = 'violent')  AS violent_count,
        COUNT(*) FILTER (WHERE offense_category = 'theft')    AS theft_count,
        COUNT(*) FILTER (WHERE offense_category = 'property') AS property_count
    FROM crime_incidents
    WHERE neighborhood_id IS NOT NULL
      AND incident_date >= CURRENT_DATE - INTERVAL '1 year'
    GROUP BY neighborhood_id, time_bucket
),

-- Anchor YoY to the dataset's most recent date (not today) so a lagging
-- data source doesn't create a false "recent drop" artifact.
data_ceiling AS (
    SELECT MAX(incident_date) AS latest FROM crime_incidents
),
current_half AS (
    SELECT neighborhood_id, COUNT(*) AS cnt
    FROM crime_incidents, data_ceiling
    WHERE neighborhood_id IS NOT NULL
      AND incident_date >= data_ceiling.latest - INTERVAL '6 months'
    GROUP BY neighborhood_id
),
prior_half AS (
    SELECT neighborhood_id, COUNT(*) AS cnt
    FROM crime_incidents, data_ceiling
    WHERE neighborhood_id IS NOT NULL
      AND incident_date >= data_ceiling.latest - INTERVAL '12 months'
      AND incident_date <  data_ceiling.latest - INTERVAL '6 months'
    GROUP BY neighborhood_id
),
yoy AS (
    SELECT
        c.neighborhood_id,
        CASE
            WHEN COALESCE(p.cnt, 0) > 0
            THEN ROUND(((c.cnt - p.cnt)::float / p.cnt * 100)::numeric, 1)
            ELSE 0
        END AS yoy_trend
    FROM current_half c
    LEFT JOIN prior_half p USING (neighborhood_id)
),

-- Attach population (fall back to NYC median of 30 000 if unknown)
with_pop AS (
    SELECT
        rc.*,
        COALESCE(n.population, 30000)       AS population,
        COALESCE(yoy.yoy_trend, 0)          AS yoy_trend
    FROM recent_counts rc
    JOIN neighborhoods n    ON n.id = rc.neighborhood_id
    LEFT JOIN yoy           ON yoy.neighborhood_id = rc.neighborhood_id
),

-- Per-1 000-resident rates + time-adjusted composite
rates AS (
    SELECT
        neighborhood_id,
        time_bucket,
        yoy_trend,
        ROUND((violent_count ::float / NULLIF(population,0) * 1000)::numeric, 4) AS violent_rate,
        ROUND((theft_count   ::float / NULLIF(population,0) * 1000)::numeric, 4) AS theft_rate,
        ROUND((property_count::float / NULLIF(population,0) * 1000)::numeric, 4) AS property_crime_rate,
        (violent_count * 3.0 + theft_count * 1.5 + property_count * 1.0)
          / NULLIF(population, 0) * 1000
          * CASE time_bucket
              WHEN 'late_night' THEN 1.4
              WHEN 'evening'    THEN 1.2
              WHEN 'afternoon'  THEN 0.9
              WHEN 'morning'    THEN 0.8
              ELSE 1.0
            END AS composite_raw
    FROM with_pop
),

-- Normalise to 0–100: 95th-percentile composite_raw → 100
p95 AS (
    SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY composite_raw) AS ceiling
    FROM rates
),
normalized AS (
    SELECT
        r.*,
        LEAST(ROUND((r.composite_raw / NULLIF(p.ceiling, 0) * 100)::numeric, 2), 100) AS composite_score
    FROM rates r
    CROSS JOIN p95 p
)

-- Replace all existing scores with freshly computed values
INSERT INTO neighborhood_scores
    (neighborhood_id, time_bucket,
     violent_rate, theft_rate, property_crime_rate,
     composite_score, risk_band, yoy_trend, computed_at)
SELECT
    neighborhood_id,
    time_bucket,
    violent_rate,
    theft_rate,
    property_crime_rate,
    composite_score,
    CASE
        WHEN composite_score <= 25 THEN 'Low'
        WHEN composite_score <= 50 THEN 'Moderate'
        WHEN composite_score <= 75 THEN 'Elevated'
        ELSE 'High'
    END AS risk_band,
    yoy_trend,
    NOW()
FROM normalized
""")


async def recompute_all_scores(db: AsyncSession) -> int:
    """
    Truncate neighborhood_scores and recompute from crime_incidents.
    Returns the number of score rows written.
    """
    log.info("Recomputing neighborhood scores...")

    await db.execute(text("TRUNCATE TABLE neighborhood_scores"))
    result = await db.execute(_RECOMPUTE_SQL)
    await db.commit()

    count = result.rowcount
    log.info("Scores written: %d rows", count)
    return count
