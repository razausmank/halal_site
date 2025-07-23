from fastapi import FastAPI
from app.routers import health, database, auth
from app.routers import restaurant
from app.routers import data_collection
from dotenv import load_dotenv

load_dotenv()
# Create FastAPI app
app = FastAPI(title="Halal Site API", version="1.0.0")

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(database.router, prefix="/db", tags=["database"])
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(restaurant.router) 
app.include_router(data_collection.router, tags=["data_collection"])