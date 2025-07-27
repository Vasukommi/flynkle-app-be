"""Simple health check endpoint."""

from fastapi import APIRouter

from app.core import success, StandardResponse

router = APIRouter()

@router.get("/health", response_model=StandardResponse, summary="Health check")
async def health() -> dict:
    """Return API health status."""
    return success({"status": "ok"}).dict()
