from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, func
from database import Base


class RedditSignal(Base):
    __tablename__ = "reddit_signals"

    id = Column(Integer, primary_key=True)
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.id"))
    subreddit = Column(String(100))
    post_title = Column(Text)
    post_body = Column(Text)
    sentiment = Column(String(20))
    safety_relevant = Column(Boolean)
    post_date = Column(DateTime)
    fetched_at = Column(DateTime, server_default=func.now())


class DemographicContext(Base):
    __tablename__ = "demographic_context"

    id = Column(Integer, primary_key=True)
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.id"))
    age_median = Column(Float)
    pct_under_25 = Column(Float)
    pct_over_65 = Column(Float)
    foot_traffic_score = Column(Float)
    late_night_activity_score = Column(Float)
    transit_isolation_score = Column(String(20))
    updated_at = Column(DateTime, server_default=func.now())
