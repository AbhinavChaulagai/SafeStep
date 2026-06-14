from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db

router = APIRouter()


@router.get("/{city}/geojson")
async def get_neighborhoods_geojson(
    city: str,
    time_bucket: str = Query(
        "evening",
        enum=["morning", "afternoon", "evening", "late_night"],
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    GeoJSON FeatureCollection for Mapbox choropleth.
    Each feature carries risk_band + score as properties.
    Geometry is topology-safe simplified (≈10 m tolerance) for fast tile rendering.
    """
    result = await db.execute(
        text("""
            SELECT
                n.id,
                n.name,
                n.borough,
                ST_AsGeoJSON(
                    ST_SimplifyPreserveTopology(n.geom, 0.0001)
                ) AS geometry,
                COALESCE(ns.risk_band,        'Low') AS risk_band,
                COALESCE(ns.composite_score,  0)     AS composite_score,
                COALESCE(ns.violent_rate,     0)     AS violent_rate,
                COALESCE(ns.theft_rate,       0)     AS theft_rate,
                COALESCE(ns.property_crime_rate, 0)  AS property_crime_rate,
                COALESCE(ns.yoy_trend,        0)     AS yoy_trend
            FROM neighborhoods n
            LEFT JOIN neighborhood_scores ns
                   ON ns.neighborhood_id = n.id
                  AND ns.time_bucket = :time_bucket
            WHERE n.city = :city
            ORDER BY n.borough, n.name
        """),
        {"city": city.lower(), "time_bucket": time_bucket},
    )
    rows = result.fetchall()

    features = []
    for row in rows:
        if not row.geometry:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": json.loads(row.geometry),
                "properties": {
                    "id": row.id,
                    "name": row.name,
                    "borough": row.borough,
                    "risk_band": row.risk_band,
                    "composite_score": float(row.composite_score),
                    "violent_rate": float(row.violent_rate),
                    "theft_rate": float(row.theft_rate),
                    "property_crime_rate": float(row.property_crime_rate),
                    "yoy_trend": float(row.yoy_trend),
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}


@router.get("/{city}")
async def get_neighborhoods(
    city: str,
    time_bucket: str = Query("evening", enum=["morning", "afternoon", "evening", "late_night"]),
    db: AsyncSession = Depends(get_db),
):
    """List of all neighborhoods with their current risk band for the chosen time bucket."""
    result = await db.execute(
        text("""
            SELECT
                n.id,
                n.name,
                n.city,
                n.borough,
                COALESCE(ns.risk_band,       'Low') AS risk_band,
                COALESCE(ns.composite_score, 0)     AS composite_score,
                COALESCE(ns.yoy_trend,       0)     AS yoy_trend
            FROM neighborhoods n
            LEFT JOIN neighborhood_scores ns
                   ON ns.neighborhood_id = n.id
                  AND ns.time_bucket = :time_bucket
            WHERE n.city = :city
            ORDER BY n.borough, n.name
        """),
        {"city": city.lower(), "time_bucket": time_bucket},
    )
    rows = result.fetchall()
    return [
        {
            "id": r.id,
            "name": r.name,
            "city": r.city,
            "borough": r.borough,
            "risk_band": r.risk_band,
            "composite_score": float(r.composite_score),
            "yoy_trend": float(r.yoy_trend),
        }
        for r in rows
    ]
