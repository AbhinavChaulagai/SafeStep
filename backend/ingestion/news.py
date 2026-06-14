"""
News alert ingestion — NewsAPI + NYT API.
Fetches articles mentioning neighborhoods with safety-related keywords.
"""

from datetime import datetime, timedelta, timezone
import httpx
from config import settings
from models.neighborhood import Neighborhood
from models.alert import NewsAlert

SAFETY_KEYWORDS = [
    "shooting", "robbery", "assault", "protest", "unrest",
    "crime", "police", "arrest", "stabbing", "riot",
]


def _build_newsapi_query(neighborhood_name: str, city: str) -> str:
    keyword_clause = " OR ".join(SAFETY_KEYWORDS[:5])
    return f'("{neighborhood_name}" OR "{city}") AND ({keyword_clause})'


async def fetch_newsapi(neighborhood: str, city: str) -> list[dict]:
    if not settings.news_api_key:
        return []
    query = _build_newsapi_query(neighborhood, city)
    from_date = (datetime.now(timezone.utc) - timedelta(hours=72)).strftime("%Y-%m-%dT%H:%M:%S")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "from": from_date,
                "sortBy": "publishedAt",
                "language": "en",
                "apiKey": settings.news_api_key,
                "pageSize": 10,
            },
        )
        resp.raise_for_status()
        return resp.json().get("articles", [])


def score_relevance(article: dict, neighborhood_name: str) -> float:
    text = (article.get("title", "") + " " + article.get("description", "")).lower()
    score = 0.0
    if neighborhood_name.lower() in text:
        score += 0.5
    for kw in SAFETY_KEYWORDS:
        if kw in text:
            score += 0.1
    return min(score, 1.0)


async def ingest(db, city: str = "nyc") -> int:
    """Fetch news for all neighborhoods in city and upsert into news_alerts."""
    # TODO: query neighborhoods, fetch articles, deduplicate by URL, upsert
    return 0
