from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_user
from app.db.database import get_db
from app.repositories import usage as usage_repo
from app.schemas import UsageRead
from app.core import success, StandardResponse

router = APIRouter(tags=["plans"])

PLANS = {
    "free": {"price": 0, "daily_messages": 20},
    "pro": {"price": 10, "daily_messages": 1000},
}

@router.get("/plans", response_model=StandardResponse, summary="Available plans")
def list_plans() -> dict:
    return success(PLANS).dict()

@router.get("/user/usage", response_model=StandardResponse, summary="User usage")
def get_usage(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    usage = usage_repo.get_usage(db, current_user.user_id)
    payload = [UsageRead.model_validate(u) for u in usage]
    return success(payload).dict()

@router.post("/user/upgrade", response_model=StandardResponse, summary="Upgrade plan (stub)")
def upgrade_plan(
    plan: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    current_user.plan = plan
    db.commit()
    return success({"detail": "plan updated"}).dict()
