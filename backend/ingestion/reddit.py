"""
Reddit ingestion — pulls posts from NYC-related subreddits and classifies them.
Uses PRAW for Reddit API access and gpt-4o-mini for safety classification.
"""

import praw
from datetime import datetime, timedelta, timezone
from config import settings
from services.llm import classify_reddit_post

NYC_SUBREDDITS = ["nyc", "AskNYC", "Brooklyn", "manhattan", "queens", "harlem", "astoria"]


def build_reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
    )


def fetch_neighborhood_posts(reddit: praw.Reddit, neighborhood_name: str, days: int = 30) -> list:
    posts = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    for sub_name in NYC_SUBREDDITS:
        sub = reddit.subreddit(sub_name)
        for submission in sub.search(neighborhood_name, sort="new", time_filter="month", limit=25):
            if datetime.fromtimestamp(submission.created_utc, tz=timezone.utc) >= cutoff:
                posts.append(submission)
    return posts


async def ingest(db, city: str = "nyc") -> int:
    """Fetch and classify Reddit posts for all neighborhoods, upsert into reddit_signals."""
    # TODO: query neighborhoods, fetch posts, classify with LLM, upsert
    return 0
