"""Application entrypoint and global configuration."""

import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.api.v1.api import api_router
from sqlalchemy.exc import SQLAlchemyError
from app.core import success

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Flynkle API", version="0.1.0")


@app.exception_handler(SQLAlchemyError)
async def handle_db_exceptions(request: Request, exc: SQLAlchemyError):
    """Return a JSON response for database errors instead of crashing."""
    logger.exception("Database error")
    resp = success(message="Database error", code=500)
    return JSONResponse(status_code=500, content=resp.dict())


@app.exception_handler(HTTPException)
async def handle_http_exceptions(request: Request, exc: HTTPException):
    """Return a consistent JSON structure for HTTP errors."""
    resp = success(message=exc.detail, code=exc.status_code)
    return JSONResponse(status_code=exc.status_code, content=resp.dict())


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception):
    """Catch-all handler for uncaught exceptions."""
    logger.exception("Unhandled error")
    resp = success(message="Internal server error", code=500)
    return JSONResponse(status_code=500, content=resp.dict())


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root() -> dict:
    logger.info("Root endpoint accessed")
    return success({"message": "Welcome to Flynkle API"}).dict()
