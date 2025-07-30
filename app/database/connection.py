from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
import os

# Use SQLite for development
DATABASE_URL = "sqlite:///./halal_site.db"

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

# Create base class for models
Base = declarative_base()

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    from sqlalchemy.orm import Session
    with Session(engine) as session:
        yield session 