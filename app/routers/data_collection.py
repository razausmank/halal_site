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
def get_location(db: Session = Depends(get_db)): 
    locations = []
    saved_count = 0
    queries = []
   
    step_size = 0.01 
    lat_length = int((max_lat - min_lat)/step_size) + 1 
    long_length = int((max_long - min_long)/step_size) + 1 
    
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    
    for i in range(lat_length): 
        lat = round(min_lat + (i * step_size), 2)
        for j in range(long_length): 
            long = round(min_long + (j * step_size), 2)
            locations.append((lat, long))
            
            # Create Google Maps API query URL for this location
            query = f"halal restaurants near {lat},{long}"
            url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&location={lat},{long}&radius=5000&key={API_KEY}"
            
            queries.append({
                "latitude": lat,
                "longitude": long,
                "query": query,
                "url": url
            })
            
            # Save each location to database
            db_location = data_collection_api_calls(
                latitude=lat,
                longitude=long,
                status="pending"
            )
            db.add(db_location)
            saved_count += 1
    
    # Commit all locations to database
    db.commit()
    
    return {
        "message": f"Successfully saved {saved_count} locations to database",
        "response": [lat_length, long_length], 
        "locations": locations,
        "saved_count": saved_count,
        "queries": queries[:5],  # Show first 5 queries as example
        "total_queries": len(queries)
    }

@router.post('/process-locations')
def process_locations(db: Session = Depends(get_db)):
    """
    Process all pending locations by executing Google Maps API calls
    and updating the database records with responses
    """
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Google Maps API key not configured")
    
    # Get all pending records
    pending_records = db.query(data_collection_api_calls).filter(
        data_collection_api_calls.status == "pending"
    ).all()
    
    if not pending_records:
        return {"message": "No pending records found", "processed": 0}
    
    processed_count = 0
    error_count = 0
    total_restaurants = 0
    
    for record in pending_records:
        try:
            # Create the Google Maps API query
            query = f"halal restaurants near {record.latitude},{record.longitude}"
            url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&location={record.latitude},{record.longitude}&radius=5000&key={API_KEY}"
            
            # Make the API call
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for bad status codes
            
            data = response.json()
            
            # Update the record with response data
            record.status = "completed"
            record.processed_at = datetime.now()
            record.response_body = data
            record.api_calls_made = 1
            
            # Count restaurants found
            if data.get("results"):
                record.restaurants_found = len(data["results"])
                total_restaurants += len(data["results"])
            else:
                record.restaurants_found = 0
            
            processed_count += 1
            
            # Commit each record individually to avoid losing all progress on error
            db.commit()
            
        except requests.exceptions.RequestException as e:
            # Handle network/API errors
            record.status = "error"
            record.error_message = f"API request failed: {str(e)}"
            record.retry_count += 1
            error_count += 1
            db.commit()
            
        except Exception as e:
            # Handle other errors
            record.status = "error"
            record.error_message = f"Processing error: {str(e)}"
            record.retry_count += 1
            error_count += 1
            db.commit()
    
    return {
        "message": f"Processing completed",
        "total_records": len(pending_records),
        "processed_successfully": processed_count,
        "errors": error_count,
        "total_restaurants_found": total_restaurants,
        "average_restaurants_per_location": total_restaurants / processed_count if processed_count > 0 else 0
    }

@router.post('/process-locations-batch')
def process_locations_batch(batch_size: int = 10, db: Session = Depends(get_db)):
    """
    Process locations in batches to avoid overwhelming the API
    """
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Google Maps API key not configured")
    
    # Get pending records with limit
    pending_records = db.query(data_collection_api_calls).filter(
        data_collection_api_calls.status == "pending"
    ).limit(batch_size).all()
    
    if not pending_records:
        return {"message": "No pending records found", "processed": 0}
    
    processed_count = 0
    error_count = 0
    total_restaurants = 0
    
    for record in pending_records:
        try:
            # Create the Google Maps API query
            query = f"halal restaurants near {record.latitude},{record.longitude}"
            url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&location={record.latitude},{record.longitude}&radius=5000&key={API_KEY}"
            
            # Make the API call
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Update the record with response data
            record.status = "completed"
            record.processed_at = datetime.now()
            record.response_body = data
            record.api_calls_made = 1
            
            # Count restaurants found
            if data.get("results"):
                record.restaurants_found = len(data["results"])
                total_restaurants += len(data["results"])
            else:
                record.restaurants_found = 0
            
            processed_count += 1
            
            # Commit each record individually
            db.commit()
            
        except requests.exceptions.RequestException as e:
            # Handle network/API errors
            record.status = "error"
            record.error_message = f"API request failed: {str(e)}"
            record.retry_count += 1
            error_count += 1
            db.commit()
            
        except Exception as e:
            # Handle other errors
            record.status = "error"
            record.error_message = f"Processing error: {str(e)}"
            record.retry_count += 1
            error_count += 1
            db.commit()
    
    return {
        "message": f"Batch processing completed",
        "batch_size": batch_size,
        "processed_successfully": processed_count,
        "errors": error_count,
        "total_restaurants_found": total_restaurants,
        "average_restaurants_per_location": total_restaurants / processed_count if processed_count > 0 else 0
    }

@router.get('/retry-failed')
def retry_failed_locations(db: Session = Depends(get_db)):
    """
    Retry processing for records that failed (status = "error")
    """
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Google Maps API key not configured")
    
    # Get failed records that haven't exceeded max retries
    failed_records = db.query(data_collection_api_calls).filter(
        data_collection_api_calls.status == "error",
        data_collection_api_calls.retry_count < data_collection_api_calls.max_retries
    ).all()
    
    if not failed_records:
        return {"message": "No failed records to retry", "retried": 0}
    
    retried_count = 0
    success_count = 0
    error_count = 0
    
    for record in failed_records:
        try:
            # Create the Google Maps API query
            query = f"halal restaurants near {record.latitude},{record.longitude}"
            url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&location={record.latitude},{record.longitude}&radius=5000&key={API_KEY}"
            
            # Make the API call
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Update the record with response data
            record.status = "completed"
            record.processed_at = datetime.now()
            record.response_body = data
            record.api_calls_made += 1
            record.error_message = None  # Clear previous error
            
            # Count restaurants found
            if data.get("results"):
                record.restaurants_found = len(data["results"])
            else:
                record.restaurants_found = 0
            
            retried_count += 1
            success_count += 1
            
            # Commit each record individually
            db.commit()
            
        except Exception as e:
            # Handle errors
            record.status = "error"
            record.error_message = f"Retry failed: {str(e)}"
            record.retry_count += 1
            retried_count += 1
            error_count += 1
            db.commit()
    
    return {
        "message": f"Retry processing completed",
        "total_retried": retried_count,
        "successful_retries": success_count,
        "failed_retries": error_count
    }

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

