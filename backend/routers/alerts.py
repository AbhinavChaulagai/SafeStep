from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from database import get_db
from models.alert import NewsAlert
from models.neighborhood import Neighborhood

router = APIRouter()


@router.get("/{city}")
async def get_city_alerts(city: str, db: AsyncSession = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(hours=72)
    result = await db.execute(
        select(NewsAlert, Neighborhood.name)
        .join(Neighborhood, NewsAlert.neighborhood_id == Neighborhood.id)
        .where(Neighborhood.city == city.lower())
        .where(NewsAlert.published_at >= cutoff)
        .order_by(NewsAlert.published_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": alert.id,
            "neighborhood": name,
            "headline": alert.headline,
            "source": alert.source,
            "url": alert.url,
            "published_at": alert.published_at,
            "relevance_score": alert.relevance_score,
        }
        for alert, name in rows
    ]
