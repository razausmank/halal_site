from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.data_collection import data_collection_api_calls
from app.models.restaurant import Restaurant
from app.schemas.data_collection import DataCollectionCreate, DataCollectionResponse, DataCollectionUpdate
from app.schemas.restaurant import RestaurantCreate
from typing import List
import requests 
import os 
import time
from datetime import datetime

router = APIRouter() 

def get_all_restaurants_for_location(lat, lng, API_KEY):
    """
    Get all restaurants for a location using Google Maps API pagination.
    Returns all results, not just the first 20.
    """
    all_results = []
    next_page_token = None
    api_calls_made = 0
    
    while True:
        # Build URL with pagination
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=restaurants near {lat},{lng}&location={lat},{lng}&radius=1200&key={API_KEY}"
        
        if next_page_token:
            url += f"&pagetoken={next_page_token}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            api_calls_made += 1
            
            if data.get("status") == "OK":
                if data.get("results"):
                    all_results.extend(data["results"])
                    print(f"  Page {api_calls_made}: Found {len(data['results'])} restaurants")
                
                # Check if there are more pages
                next_page_token = data.get("next_page_token")
                if not next_page_token:
                    break
                
                # Google requires a short delay between pagination requests
                print(f"  Waiting 2 seconds for next page...")
                time.sleep(2)
            else:
                print(f"  API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
                break
                
        except Exception as e:
            print(f"  Error making API call: {str(e)}")
            break
    
    print(f"  Total restaurants found: {len(all_results)} (in {api_calls_made} API calls)")
    return all_results

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
            query = f" restaurants near {lat},{long}"
            url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&location={lat},{long}&radius=1500&key={API_KEY}"
            
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
def process_locations(batch_size: int = 20, db: Session = Depends(get_db)):
    """
    Process all pending locations by executing Google Maps API calls
    and updating the database records with responses. Uses internal batching with rate limiting.
    """
    import time
    
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Google Maps API key not configured")
    
    # Get all pending records
    pending_records = db.query(data_collection_api_calls).filter(
        data_collection_api_calls.status == "pending"
    ).all()
    
    if not pending_records:
        return {"message": "No pending records found", "processed": 0}
    
    total_records = len(pending_records)
    processed_count = 0
    error_count = 0
    total_restaurants = 0
    batch_number = 0
    
    # Process in batches
    for i in range(0, total_records, batch_size):
        batch_number += 1
        batch_start = i
        batch_end = min(i + batch_size, total_records)
        current_batch = pending_records[batch_start:batch_end]
        
        print(f"Processing batch {batch_number}: locations {batch_start + 1}-{batch_end} of {total_records}")
        
        # Process current batch
        for record in current_batch:
            try:
                # Get all restaurants for this location using pagination
                all_restaurants_for_location = get_all_restaurants_for_location(
                    record.latitude, record.longitude, API_KEY
                )
                
                # Update the record with response data
                record.status = "completed"
                record.processed_at = datetime.now()
                record.response_body = {"results": all_restaurants_for_location}
                record.api_calls_made = len(all_restaurants_for_location) // 20 + 1  # Estimate API calls made
                
                # Count restaurants found
                if all_restaurants_for_location:
                    record.restaurants_found = len(all_restaurants_for_location)
                    total_restaurants += len(all_restaurants_for_location)
                    print(f"Found {len(all_restaurants_for_location)} restaurants at location {record.latitude},{record.longitude}")
                else:
                    record.restaurants_found = 0
                    print(f"No restaurants found at location {record.latitude},{record.longitude}")
                
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
        
        # Add delay between batches (except for the last batch)
        if batch_end < total_records:
            print(f"Waiting 30 seconds before next batch...")
            time.sleep(30)
    
    return {
        "message": "Processing completed",
        "batch_size": batch_size,
        "total_batches": batch_number,
        "total_records": total_records,
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
            # Get all restaurants for this location using pagination
            all_restaurants_for_location = get_all_restaurants_for_location(
                record.latitude, record.longitude, API_KEY
            )
            
            # Update the record with response data
            record.status = "completed"
            record.processed_at = datetime.now()
            record.response_body = {"results": all_restaurants_for_location}
            record.api_calls_made += len(all_restaurants_for_location) // 20 + 1  # Estimate API calls made
            record.error_message = None  # Clear previous error
            
            # Count restaurants found
            if all_restaurants_for_location:
                record.restaurants_found = len(all_restaurants_for_location)
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

@router.get("/fetch-restaurant-details")
def fetch_restaurant_details(batch_size: int = 20, db: Session = Depends(get_db)):
    """
    Fetch all restaurants from completed data collection records and get detailed information
    from Google Maps Places API for each restaurant. Uses internal batching with rate limiting.
    """
    import time
    
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Google Maps API key not configured")
    
    # Get all completed records
    completed_records = db.query(data_collection_api_calls).filter(
        data_collection_api_calls.status == "completed"
    ).all()
    
    if not completed_records:
        return {"message": "No completed records found", "processed": 0}
    
    all_restaurants = []
    processed_count = 0
    error_count = 0
    batch_number = 0
    
    # Collect all restaurants first
    all_restaurant_data = []
    for record in completed_records:
        if not record.response_body or "results" not in record.response_body:
            continue
            
        restaurants = record.response_body.get("results", [])
        for restaurant in restaurants:
            place_id = restaurant.get("place_id")
            if place_id:
                all_restaurant_data.append({
                    "restaurant": restaurant,
                    "record": record
                })
    
    total_restaurants = len(all_restaurant_data)
    
    # Process in batches
    for i in range(0, total_restaurants, batch_size):
        batch_number += 1
        batch_start = i
        batch_end = min(i + batch_size, total_restaurants)
        current_batch = all_restaurant_data[batch_start:batch_end]
        
        print(f"Processing batch {batch_number}: restaurants {batch_start + 1}-{batch_end} of {total_restaurants}")
        
        # Process current batch
        for item in current_batch:
            restaurant = item["restaurant"]
            record = item["record"]
            
            try:
                place_id = restaurant.get("place_id")
                
                # Check if restaurant already exists in the Restaurant table
                existing_restaurant = db.query(Restaurant).filter(Restaurant.place_id == place_id).first()
                if existing_restaurant:
                    print(f"Skipping place_id {place_id} (already exists)")
                    continue

                # Make detailed API call to Google Maps Places API
                details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,opening_hours,price_level,types,business_status,geometry,photos,reviews,url&key={API_KEY}"
                
                response = requests.get(details_url)
                response.raise_for_status()
                
                details_data = response.json()
                
                if details_data.get("status") == "OK":
                    restaurant_details = details_data.get("result", {})
                    
                    # Extract address components
                    address_components = restaurant_details.get("address_components", [])
                    city = None
                    state = None
                    country = None
                    
                    for component in address_components:
                        types = component.get("types", [])
                        if "locality" in types:
                            city = component.get("long_name")
                        elif "administrative_area_level_1" in types:
                            state = component.get("long_name")
                        elif "country" in types:
                            country = component.get("long_name")
                    
                    # Create restaurant data for database
                    restaurant_data = {
                        "place_id": place_id,
                        "name": restaurant_details.get("name"),
                        "description": restaurant_details.get("editorial_summary", {}).get("overview"),
                        "address": restaurant_details.get("formatted_address"),
                        "city": city,
                        "state": state,
                        "country": country,
                        "latitude": restaurant_details.get("geometry", {}).get("location", {}).get("lat"),
                        "longitude": restaurant_details.get("geometry", {}).get("location", {}).get("lng"),
                        "phone": restaurant_details.get("formatted_phone_number"),
                        "website": restaurant_details.get("website"),
                        "opening_hours": str(restaurant_details.get("opening_hours", {}).get("weekday_text", [])) if restaurant_details.get("opening_hours") else None,
                        "cuisine_type": ", ".join(restaurant_details.get("types", [])),
                        "price_range": "$" * restaurant_details.get("price_level", 0) if restaurant_details.get("price_level") else None,
                        "halal_status": None,  # Halal status needs to be verified manually
                        "rating": restaurant_details.get("rating"),
                        "scraped_json": restaurant_details,
                        "additional_info": f"User ratings: {restaurant_details.get('user_ratings_total', 0)}"
                    }
                    
                    # Create and save restaurant to database
                    try:
                        db_restaurant = Restaurant(**restaurant_data)
                        db.add(db_restaurant)
                        db.commit()
                        db.refresh(db_restaurant)
                        print(f"Saved restaurant: {restaurant_data['name']} (ID: {db_restaurant.id})")
                    except Exception as db_error:
                        print(f"Database error saving restaurant {restaurant_data['name']}: {str(db_error)}")
                        db.rollback()
                        error_count += 1
                        continue
                    
                    # Combine basic info with detailed info for response
                    enhanced_restaurant = {
                        "place_id": place_id,
                        "name": restaurant.get("name"),
                        "basic_info": restaurant,
                        "detailed_info": restaurant_details,
                        "source_location": {
                            "latitude": record.latitude,
                            "longitude": record.longitude,
                            "record_id": record.id
                        },
                        "database_id": db_restaurant.id
                    }
                    
                    all_restaurants.append(enhanced_restaurant)
                    processed_count += 1
                    
                else:
                    error_count += 1
                    print(f"API error for place_id {place_id}: {details_data.get('status')}")
                    
            except requests.exceptions.RequestException as e:
                error_count += 1
                print(f"Request error for restaurant {restaurant.get('name', 'Unknown')}: {str(e)}")
                
            except Exception as e:
                error_count += 1
                print(f"Error processing restaurant {restaurant.get('name', 'Unknown')}: {str(e)}")
        
        # Add delay between batches (except for the last batch)
        if batch_end < total_restaurants:
            print(f"Waiting 30 seconds before next batch...")
            time.sleep(30)
    
    return {
        "message": "Restaurant details fetched successfully",
        "batch_size": batch_size,
        "total_batches": batch_number,
        "total_restaurants_processed": processed_count,
        "total_restaurants_found": len(all_restaurants),
        "errors": error_count,
        "restaurants": all_restaurants
    }

@router.get("/restaurant-stats")
def get_restaurant_stats(db: Session = Depends(get_db)):
    """
    Get statistics about collected restaurants and data collection progress
    """
    # Count restaurants in database
    total_restaurants = db.query(Restaurant).count()
    
    # Count restaurants by city
    city_stats = db.query(Restaurant.city, db.func.count(Restaurant.id)).group_by(Restaurant.city).all()
    
    # Count restaurants by rating
    rating_stats = db.query(Restaurant.rating, db.func.count(Restaurant.id)).group_by(Restaurant.rating).all()
    
    # Count restaurants by price range
    price_stats = db.query(Restaurant.price_range, db.func.count(Restaurant.id)).group_by(Restaurant.price_range).all()
    
    # Get data collection progress
    total_locations = db.query(data_collection_api_calls).count()
    completed_locations = db.query(data_collection_api_calls).filter(data_collection_api_calls.status == "completed").count()
    pending_locations = db.query(data_collection_api_calls).filter(data_collection_api_calls.status == "pending").count()
    error_locations = db.query(data_collection_api_calls).filter(data_collection_api_calls.status == "error").count()
    
    # Get API usage statistics
    total_api_calls = db.query(db.func.sum(data_collection_api_calls.api_calls_made)).scalar() or 0
    total_restaurants_found = db.query(db.func.sum(data_collection_api_calls.restaurants_found)).scalar() or 0
    
    # Calculate averages
    avg_restaurants_per_location = round(total_restaurants_found / completed_locations, 2) if completed_locations > 0 else 0
    avg_api_calls_per_location = round(total_api_calls / completed_locations, 2) if completed_locations > 0 else 0
    
    return {
        "restaurant_database": {
            "total_restaurants": total_restaurants,
            "by_city": dict(city_stats) if city_stats else {},
            "by_rating": dict(rating_stats) if rating_stats else {},
            "by_price_range": dict(price_stats) if price_stats else {}
        },
        "data_collection_progress": {
            "total_locations": total_locations,
            "completed": completed_locations,
            "pending": pending_locations,
            "errors": error_locations,
            "completion_percentage": round((completed_locations / total_locations * 100), 2) if total_locations > 0 else 0
        },
        "api_usage_statistics": {
            "total_api_calls_made": total_api_calls,
            "total_restaurants_found": total_restaurants_found,
            "average_restaurants_per_location": avg_restaurants_per_location,
            "average_api_calls_per_location": avg_api_calls_per_location,
            "efficiency_ratio": round(total_restaurants_found / total_api_calls, 2) if total_api_calls > 0 else 0
        }
    }

