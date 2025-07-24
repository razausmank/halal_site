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


43.4767105,-79.6323979
43.6074866,-79.8083237
43.6311091,-79.6937843
43.6285557,-79.6764448

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
    
    return {"repsonse" : [lat_length, long_length], 
            "locations" : locations }