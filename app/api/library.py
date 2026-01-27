from fastapi import APIRouter
from app.services.library_service import get_library

router = APIRouter(tags=["library"])

@router.get("/")
def list_library():
    return get_library()

# define endpoint librarry
