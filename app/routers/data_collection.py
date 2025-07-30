from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.data_collection import data_collection_api_calls
from app.schemas.data_collection import DataCollectionCreate, DataCollectionResponse, DataCollectionUpdate
from typing import List
import requests 
import os 
from datetime import datetime

router = APIRouter() 

@router.get('/datacheck')
def get_data(): 
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY') 
    city = "San Francisco"
    query = f"restaurants in {city}"
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={API_KEY}"
    
    response = requests.get(url)
    data = response.json()
        
    return {"response": data}

# Database coordinates
min_lat= 43.47
max_lat = 43.63
min_long = -79.81
max_long = -79.63

@router.get('/get-locations')
def get_location(): 
    locations = [ ]
   
    step_size = 0.01 
    lat_length = int((max_lat - min_lat)/step_size) + 1 
    long_length = int((max_long - min_long)/step_size) + 1 
    
    for i in range(lat_length): 
        lat =  round(min_lat + (i * step_size),2)
        for j in range(long_length): 
            long = round(min_long + ( j * step_size),2)
            locations.append((lat,long)) 
    
    return {"response" : [lat_length, long_length], 
            "locations" : locations }

# CRUD operations for data collection
@router.post("/data-collection/", response_model=DataCollectionResponse)
def create_data_collection(data: DataCollectionCreate, db: Session = Depends(get_db)):
    db_data = data_collection_api_calls(**data.dict())
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

@router.get("/data-collection/", response_model=List[DataCollectionResponse])
def get_data_collections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    data_collections = db.query(data_collection_api_calls).offset(skip).limit(limit).all()
    return data_collections

@router.get("/data-collection/{data_id}", response_model=DataCollectionResponse)
def get_data_collection(data_id: int, db: Session = Depends(get_db)):
    data_collection = db.query(data_collection_api_calls).filter(data_collection_api_calls.id == data_id).first()
    if data_collection is None:
        raise HTTPException(status_code=404, detail="Data collection not found")
    return data_collection

@router.put("/data-collection/{data_id}", response_model=DataCollectionResponse)
def update_data_collection(data_id: int, data: DataCollectionUpdate, db: Session = Depends(get_db)):
    db_data = db.query(data_collection_api_calls).filter(data_collection_api_calls.id == data_id).first()
    if db_data is None:
        raise HTTPException(status_code=404, detail="Data collection not found")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_data, key, value)
    
    db.commit()
    db.refresh(db_data)
    return db_data

@router.delete("/data-collection/{data_id}")
def delete_data_collection(data_id: int, db: Session = Depends(get_db)):
    db_data = db.query(data_collection_api_calls).filter(data_collection_api_calls.id == data_id).first()
    if db_data is None:
        raise HTTPException(status_code=404, detail="Data collection not found")
    
    db.delete(db_data)
    db.commit()
    return {"detail": "Data collection deleted"}