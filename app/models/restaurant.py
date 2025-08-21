from sqlalchemy import Column, Integer, String, Float, Text, JSON
from app.database.connection import Base

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String, nullable=True, unique=True, index=True)  # Google Maps place_id for duplicate checking
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    opening_hours = Column(String, nullable=True)
    cuisine_type = Column(String, nullable=True)
    price_range = Column(String, nullable=True)
    halal_status = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    scraped_json = Column(JSON, nullable=True)
    additional_info = Column(Text, nullable=True) 