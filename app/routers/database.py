from fastapi import APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.connection import engine

router = APIRouter()

@router.get("/db-check")
def db_check():
    try:
        with Session(engine) as session:
            # Simple query to test connection
            session.execute(text("SELECT 1"))
        return {"db_status": "connected"}
    except Exception as e:
        return {"db_status": "error", "details": str(e)} 