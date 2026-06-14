from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, func, Index
from database import Base


class NewsAlert(Base):
    __tablename__ = "news_alerts"
    __table_args__ = (
        Index("ix_news_alerts_neighborhood_published", "neighborhood_id", "published_at"),
    )

    id = Column(Integer, primary_key=True)
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.id"))
    headline = Column(Text)
    source = Column(String(100))
    url = Column(Text)
    published_at = Column(DateTime)
    relevance_score = Column(Float)
    fetched_at = Column(DateTime, server_default=func.now())
