from pydantic import BaseModel, Field
from typing import Optional, Any

class RestaurantBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    halal_status: Optional[str] = None
    rating: Optional[float] = None
    scraped_json: Optional[Any] = None
    additional_info: Optional[str] = None

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantUpdate(RestaurantBase):
    pass

class RestaurantRead(RestaurantBase):
    id: int

    class Config:
        orm_mode = True 