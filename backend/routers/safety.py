from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.scoring import calculate_risk_band
from services.llm import generate_safety_briefing

router = APIRouter()


@router.get("/compare")
async def compare_neighborhoods(
    city: str = Query(...),
    areas: str = Query(..., description="Comma-separated neighborhood names (exactly 2)"),
    time_bucket: str = Query("evening", enum=["morning", "afternoon", "evening", "late_night"]),
    db: AsyncSession = Depends(get_db),
):
    area_list = [a.strip() for a in areas.split(",")]
    if len(area_list) != 2:
        raise HTTPException(status_code=400, detail="Exactly two areas required for comparison")

    results = []
    for name in area_list:
        row = await _get_neighborhood_data(city, name, time_bucket, "solo", db)
        if row:
            results.append(row)

    lower = ""
    if len(results) == 2:
        scores = [r["crime_stats"].get("composite_score", 0) for r in results]
        lower = results[0]["neighborhood"] if scores[0] <= scores[1] else results[1]["neighborhood"]

    return {"areas": results, "lower_risk_at_time": lower}


@router.get("/{city}/{neighborhood}")
async def get_neighborhood_safety(
    city: str,
    neighborhood: str,
    time_bucket: str = Query("evening", enum=["morning", "afternoon", "evening", "late_night"]),
    traveler_type: str = Query("solo", enum=["solo", "couple", "family", "nightlife"]),
    db: AsyncSession = Depends(get_db),
):
    data = await _get_neighborhood_data(city, neighborhood, time_bucket, traveler_type, db)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Neighborhood '{neighborhood}' not found in {city}")
    return data


# ── shared helper ─────────────────────────────────────────────────────────────

async def _get_neighborhood_data(
    city: str,
    neighborhood: str,
    time_bucket: str,
    traveler_type: str,
    db: AsyncSession,
) -> dict | None:
    # Resolve neighborhood → id (case-insensitive partial match)
    result = await db.execute(
        text("""
            SELECT id, name, borough
            FROM neighborhoods
            WHERE city = :city
              AND LOWER(name) = LOWER(:name)
            LIMIT 1
        """),
        {"city": city.lower(), "name": neighborhood},
    )
    row = result.one_or_none()
    if row is None:
        # Fall back to partial match
        result = await db.execute(
            text("""
                SELECT id, name, borough
                FROM neighborhoods
                WHERE city = :city
                  AND LOWER(name) LIKE LOWER(:pattern)
                ORDER BY name
                LIMIT 1
            """),
            {"city": city.lower(), "pattern": f"%{neighborhood}%"},
        )
        row = result.one_or_none()
    if row is None:
        return None

    n_id, n_name, borough = row.id, row.name, row.borough

    # Score for requested time bucket
    score_data = await calculate_risk_band(n_id, time_bucket, db)

    # Crime stats row
    stats_result = await db.execute(
        text("""
            SELECT violent_rate, theft_rate, property_crime_rate, yoy_trend
            FROM neighborhood_scores
            WHERE neighborhood_id = :nid AND time_bucket = :tb
            LIMIT 1
        """),
        {"nid": n_id, "tb": time_bucket},
    )
    stats = stats_result.one_or_none()

    # Top offense type
    top_result = await db.execute(
        text("""
            SELECT offense_category, COUNT(*) AS cnt
            FROM crime_incidents
            WHERE neighborhood_id = :nid AND time_bucket = :tb
              AND incident_date >= CURRENT_DATE - INTERVAL '1 year'
            GROUP BY offense_category
            ORDER BY cnt DESC
            LIMIT 1
        """),
        {"nid": n_id, "tb": time_bucket},
    )
    top = top_result.one_or_none()

    trend = stats.yoy_trend if stats else 0.0
    trend_str = f"{'down' if trend < 0 else 'up'} {abs(trend):.1f}% vs prior 6 months"

    crime_stats = {
        "composite_score": score_data["composite_score"],
        "violent_rate": float(stats.violent_rate) if stats else 0.0,
        "theft_rate": float(stats.theft_rate) if stats else 0.0,
        "property_crime_rate": float(stats.property_crime_rate) if stats else 0.0,
        "top_offense": top.offense_category if top else "unknown",
        "yoy_trend": trend_str,
    }

    # Active news alerts (last 72 h)
    alerts_result = await db.execute(
        text("""
            SELECT id, headline, source, url, published_at, relevance_score
            FROM news_alerts
            WHERE neighborhood_id = :nid
              AND published_at >= NOW() - INTERVAL '72 hours'
            ORDER BY relevance_score DESC
            LIMIT 5
        """),
        {"nid": n_id},
    )
    alerts = [
        {
            "id": a.id,
            "headline": a.headline,
            "source": a.source,
            "url": a.url,
            "published_at": str(a.published_at),
            "relevance_score": float(a.relevance_score or 0),
        }
        for a in alerts_result.fetchall()
    ]

    # Reddit sentiment summary
    reddit_result = await db.execute(
        text("""
            SELECT sentiment, COUNT(*) AS cnt
            FROM reddit_signals
            WHERE neighborhood_id = :nid
              AND safety_relevant = true
              AND post_date >= NOW() - INTERVAL '30 days'
            GROUP BY sentiment
            ORDER BY cnt DESC
        """),
        {"nid": n_id},
    )
    reddit_rows = reddit_result.fetchall()
    post_count = sum(r.cnt for r in reddit_rows)
    dominant = reddit_rows[0].sentiment if reddit_rows else "neutral"

    # Nearby lower-risk neighborhoods (same borough, lower composite score)
    nearby_result = await db.execute(
        text("""
            SELECT n2.name
            FROM neighborhoods n2
            JOIN neighborhood_scores ns2
              ON ns2.neighborhood_id = n2.id AND ns2.time_bucket = :tb
            WHERE n2.city = :city
              AND n2.borough = :borough
              AND n2.id <> :nid
              AND ns2.composite_score < :score
            ORDER BY ns2.composite_score ASC
            LIMIT 3
        """),
        {
            "city": city.lower(),
            "borough": borough,
            "nid": n_id,
            "score": score_data["composite_score"],
            "tb": time_bucket,
        },
    )
    nearby_safer = [r.name for r in nearby_result.fetchall()]

    # Build context and generate LLM briefing (falls back to rule-based if no API key)
    context = {
        "neighborhood": n_name,
        "city": city,
        "time_requested": time_bucket,
        "risk_band": score_data["risk_band"],
        "crime_stats": crime_stats,
        "news_signals": [f"{a['headline']} ({a['source']})" for a in alerts],
        "reddit_sentiment": {
            "summary": "",
            "post_count_30d": post_count,
            "dominant_sentiment": dominant,
        },
        "demographic_context": {
            "population_density": "medium",
            "late_night_activity": "unknown",
            "transit_isolation": "unknown",
            "tourist_density": "medium",
        },
        "nearby_safer": nearby_safer,
        "traveler_type": traveler_type,
    }
    llm_briefing = await generate_safety_briefing(context)

    return {
        "neighborhood": n_name,
        "city": city,
        "borough": borough,
        "risk_band": score_data["risk_band"],
        "crime_stats": crime_stats,
        "news_alerts": alerts,
        "reddit_summary": {
            "summary": "",
            "post_count_30d": post_count,
            "dominant_sentiment": dominant,
        },
        "llm_briefing": llm_briefing,
        "nearby_safer": nearby_safer,
    }
