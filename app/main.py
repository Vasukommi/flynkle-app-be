import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.api.v1.api import api_router
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Flynkle API", version="0.1.0")


@app.exception_handler(SQLAlchemyError)
async def handle_db_exceptions(request: Request, exc: SQLAlchemyError):
    """Return a JSON response for database errors instead of crashing."""
    logger.exception("Database error")
    return JSONResponse(status_code=500, content={"detail": "Database error"})

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
    return {"message": "Welcome to Flynkle API"}
