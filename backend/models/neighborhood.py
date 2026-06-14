from sqlalchemy import Column, Integer, String, Float, DateTime, func
from geoalchemy2 import Geometry
from database import Base


class Neighborhood(Base):
    __tablename__ = "neighborhoods"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    borough = Column(String(100))
    geom = Column(Geometry("MULTIPOLYGON", srid=4326))
    population = Column(Integer)
    population_density = Column(Float)
    median_income = Column(Integer)
    tourist_density = Column(String(20))
    business_density_score = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
