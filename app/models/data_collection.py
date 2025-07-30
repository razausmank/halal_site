from sqlalchemy import Column, Integer, String, DateTime, Boolean,Float,JSON,Text
from sqlalchemy.sql import func
from app.database.connection import Base

class data_collection_api_calls(Base): 
    __tablename__ = 'data_collection_api_calls'
    
    id =Column(Integer, primary_key=True)
    latitude = Column(Float,nullable=False)
    longitude = Column(Float,nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    restaurants_found = Column(Integer,default=0)
    api_calls_made = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    response_body = Column(JSON)