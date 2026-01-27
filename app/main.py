from fastapi import FastAPI
from app.api.library import router as library_router

app = FastAPI(title="Mangareader")
app.include_router(library_router, prefix="/library")
