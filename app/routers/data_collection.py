from fastapi import APIRouter
import requests 
import os 

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