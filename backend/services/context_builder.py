from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.neighborhood import Neighborhood
from models.crime import NeighborhoodScore
from models.alert import NewsAlert
from models.reddit_signal import RedditSignal, DemographicContext


async def build_llm_context(
    neighborhood: Neighborhood,
    time_bucket: str,
    traveler_type: str,
    score_data: dict,
    db: AsyncSession,
) -> dict:
    crime_stats = await _get_crime_stats(neighborhood.id, time_bucket, score_data, db)
    news_signals = await _get_news_signals(neighborhood.id, db)
    reddit_sentiment = await _get_reddit_sentiment(neighborhood.id, db)
    demographic = await _get_demographic(neighborhood.id, db)
    nearby_safer = await _get_nearby_safer(neighborhood, score_data["risk_band"], db)

    return {
        "neighborhood": neighborhood.name,
        "city": neighborhood.city,
        "time_requested": time_bucket,
        "risk_band": score_data["risk_band"],
        "crime_stats": crime_stats,
        "news_signals": news_signals,
        "reddit_sentiment": reddit_sentiment,
        "demographic_context": demographic,
        "nearby_safer": nearby_safer,
        "traveler_type": traveler_type,
    }


async def _get_crime_stats(
    neighborhood_id: int, time_bucket: str, score_data: dict, db: AsyncSession
) -> dict:
    result = await db.execute(
        select(NeighborhoodScore).where(
            NeighborhoodScore.neighborhood_id == neighborhood_id,
            NeighborhoodScore.time_bucket == time_bucket,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return {
            "violent_rate": 0.0,
            "theft_rate": 0.0,
            "property_crime_rate": 0.0,
            "top_offense": "unknown",
            "yoy_trend": "no trend data",
        }
    trend = row.yoy_trend or 0.0
    direction = "down" if trend < 0 else "up"
    return {
        "violent_rate": row.violent_rate,
        "theft_rate": row.theft_rate,
        "property_crime_rate": row.property_crime_rate,
        "top_offense": "theft",  # TODO: derive from crime_incidents aggregation
        "yoy_trend": f"{direction} {abs(trend):.1f}% vs last year",
    }


async def _get_news_signals(neighborhood_id: int, db: AsyncSession) -> list[str]:
    cutoff = datetime.utcnow() - timedelta(hours=72)
    result = await db.execute(
        select(NewsAlert)
        .where(NewsAlert.neighborhood_id == neighborhood_id)
        .where(NewsAlert.published_at >= cutoff)
        .order_by(NewsAlert.relevance_score.desc())
        .limit(5)
    )
    alerts = result.scalars().all()
    return [f"{a.headline} ({a.source})" for a in alerts]


async def _get_reddit_sentiment(neighborhood_id: int, db: AsyncSession) -> dict:
    cutoff = datetime.utcnow() - timedelta(days=30)
    result = await db.execute(
        select(RedditSignal)
        .where(RedditSignal.neighborhood_id == neighborhood_id)
        .where(RedditSignal.safety_relevant == True)
        .where(RedditSignal.post_date >= cutoff)
    )
    posts = result.scalars().all()
    if not posts:
        return {"summary": "", "post_count_30d": 0, "dominant_sentiment": "neutral"}

    sentiment_counts: dict[str, int] = {}
    for p in posts:
        sentiment_counts[p.sentiment] = sentiment_counts.get(p.sentiment, 0) + 1
    dominant = max(sentiment_counts, key=lambda k: sentiment_counts[k])

    return {
        "summary": "",  # filled by llm.py pre-summarization
        "post_count_30d": len(posts),
        "dominant_sentiment": dominant,
    }


async def _get_demographic(neighborhood_id: int, db: AsyncSession) -> dict:
    result = await db.execute(
        select(DemographicContext).where(DemographicContext.neighborhood_id == neighborhood_id)
    )
    demo = result.scalar_one_or_none()
    return {
        "population_density": "medium",
        "late_night_activity": demo.late_night_activity_score if demo else "unknown",
        "transit_isolation": demo.transit_isolation_score if demo else "unknown",
        "tourist_density": "medium",
    }


async def _get_nearby_safer(
    neighborhood: Neighborhood, current_band: str, db: AsyncSession
) -> list[str]:
    # TODO: spatial query for neighboring areas with lower risk bands
    return []
