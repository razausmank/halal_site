from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/hello")
def hello():
    return {"message": "Hello, world!"} 