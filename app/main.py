from fastapi import FastAPI
from app.routers import health, database

# Create FastAPI app
app = FastAPI(title="Halal Site API", version="1.0.0")

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(database.router, prefix="/db", tags=["database"]) 