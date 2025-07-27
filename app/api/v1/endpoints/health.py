"""Simple health check endpoint."""

import logging
from fastapi import APIRouter

from app.core import success, StandardResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health", response_model=StandardResponse, summary="Health check")
async def health() -> dict:
    """Return API health status."""
    logger.debug("Health check requested")
    return success({"status": "ok"}).dict()
