from sqlalchemy import Column, Integer, String, Float, Date, Time, DateTime, ForeignKey, func, Index
from database import Base


class CrimeIncident(Base):
    __tablename__ = "crime_incidents"
    __table_args__ = (
        Index("ix_crime_neighborhood_time_category", "neighborhood_id", "time_bucket", "offense_category"),
    )

    id = Column(Integer, primary_key=True)
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.id"))
    city = Column(String(100), nullable=False)
    offense_category = Column(String(100))
    offense_description = Column(String(255))
    incident_date = Column(Date)
    incident_time = Column(Time)
    time_bucket = Column(String(20))
    lat = Column(Float)
    lng = Column(Float)
    source = Column(String(50))
    external_id = Column(String(100), unique=True)
    created_at = Column(DateTime, server_default=func.now())


class NeighborhoodScore(Base):
    __tablename__ = "neighborhood_scores"

    id = Column(Integer, primary_key=True)
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.id"))
    time_bucket = Column(String(20))
    violent_rate = Column(Float)
    theft_rate = Column(Float)
    property_crime_rate = Column(Float)
    composite_score = Column(Float)
    risk_band = Column(String(20))
    yoy_trend = Column(Float)
    computed_at = Column(DateTime, server_default=func.now())
