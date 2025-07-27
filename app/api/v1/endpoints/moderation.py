import logging
from uuid import uuid4
from typing import List

from fastapi import APIRouter

from app.core import success, StandardResponse

router = APIRouter(prefix="/moderation", tags=["moderation"])

logger = logging.getLogger(__name__)

_STAGED: List[dict] = []


@router.post("/stage-in", response_model=StandardResponse, summary="Stage incoming message")
def stage_in(message: str) -> dict:
    item = {"id": str(uuid4()), "direction": "in", "message": message}
    _STAGED.append(item)
    logger.info("Staged incoming message %s", item["id"])
    return success(item).dict()


@router.post("/stage-out", response_model=StandardResponse, summary="Stage outgoing message")
def stage_out(message: str) -> dict:
    item = {"id": str(uuid4()), "direction": "out", "message": message}
    _STAGED.append(item)
    logger.info("Staged outgoing message %s", item["id"])
    return success(item).dict()


@router.get("", response_model=StandardResponse, summary="List staged messages")
def list_items() -> dict:
    return success(list(_STAGED)).dict()
