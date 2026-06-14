"""
APScheduler cron jobs for SafeStep data ingestion and score recomputation.
Attach to FastAPI lifespan or run standalone.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from database import AsyncSessionLocal
from ingestion import nyc_crime, news, reddit, census
from services.scoring import recompute_all_scores

scheduler = AsyncIOScheduler()


def setup_jobs() -> None:
    scheduler.add_job(_pull_crime, IntervalTrigger(hours=6), id="crime_incidents", replace_existing=True)
    scheduler.add_job(_pull_news, IntervalTrigger(hours=2), id="news_alerts", replace_existing=True)
    scheduler.add_job(_pull_reddit, IntervalTrigger(hours=24), id="reddit_posts", replace_existing=True)
    scheduler.add_job(_recompute_scores, CronTrigger(hour=2, minute=0), id="recompute_scores", replace_existing=True)
    scheduler.add_job(_refresh_census, CronTrigger(day_of_week="mon", hour=3), id="census", replace_existing=True)


async def _pull_crime() -> None:
    async with AsyncSessionLocal() as db:
        count = await nyc_crime.ingest(db, incremental=True)
        print(f"[scheduler] Ingested {count} crime records")


async def _pull_news() -> None:
    async with AsyncSessionLocal() as db:
        count = await news.ingest(db)
        print(f"[scheduler] Ingested {count} news alerts")


async def _pull_reddit() -> None:
    async with AsyncSessionLocal() as db:
        count = await reddit.ingest(db)
        print(f"[scheduler] Ingested {count} Reddit signals")


async def _recompute_scores() -> None:
    async with AsyncSessionLocal() as db:
        await recompute_all_scores(db)
        print("[scheduler] Scores recomputed")


async def _refresh_census() -> None:
    async with AsyncSessionLocal() as db:
        count = await census.ingest(db)
        print(f"[scheduler] Refreshed census data for {count} neighborhoods")
