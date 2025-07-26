from fastapi import FastAPI

from app.api.v1.api import api_router

app = FastAPI(title="Flynkle API", version="0.1.0")

app.include_router(api_router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {"message": "Welcome to Flynkle API"}
