from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class DataCollectionBase(BaseModel):
    latitude: float
    longitude: float
    status: str = "pending"
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    restaurants_found: int = 0
    api_calls_made: int = 0
    retry_count: int = 0
    max_retries: int = 3
    response_body: Optional[Dict[str, Any]] = None

class DataCollectionCreate(DataCollectionBase):
    pass

class DataCollectionUpdate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: Optional[str] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    restaurants_found: Optional[int] = None
    api_calls_made: Optional[int] = None
    retry_count: Optional[int] = None
    max_retries: Optional[int] = None
    response_body: Optional[Dict[str, Any]] = None

class DataCollectionResponse(DataCollectionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models