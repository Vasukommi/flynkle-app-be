from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_user
from app.db.database import get_db
from app.repositories import usage as usage_repo
from app.repositories import conversation as convo_repo
from app.schemas import UsageRead
from app.core import success, StandardResponse, PLANS
from app.services.billing import charge_plan

import logging

router = APIRouter(tags=["plans"])
logger = logging.getLogger(__name__)


@router.get("/plans", response_model=StandardResponse, summary="Available plans")
def list_plans() -> dict:
    """Return subscription plans with feature limits."""
    logger.debug("Listing plans")
    return success(PLANS).dict()


@router.get("/user/usage", response_model=StandardResponse, summary="User usage")
def get_usage(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info("Fetching usage for %s", current_user.user_id)
    usage = usage_repo.get_usage(db, current_user.user_id)
    payload = [UsageRead.model_validate(u) for u in usage]
    return success(payload).dict()


@router.post("/user/upgrade", response_model=StandardResponse, summary="Upgrade plan")
def upgrade_plan(
    plan: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Change a user's subscription plan with basic validation."""
    if plan not in PLANS:
        logger.warning("Invalid plan '%s' requested by %s", plan, current_user.user_id)
        raise HTTPException(status_code=400, detail="Invalid plan")
    if plan == current_user.plan:
        logger.info("User %s already on %s plan", current_user.user_id, plan)
        return success({"detail": "plan unchanged"}).dict()

    # Prevent downgrades when over quota
    new_plan = PLANS[plan]
    convo_count = convo_repo.count_conversations(db, current_user.user_id)
    if convo_count > new_plan["max_conversations"]:
        raise HTTPException(status_code=400, detail="Over conversation quota")
    daily = usage_repo.get_daily_usage(db, current_user.user_id, date.today())
    if daily:
        if daily.message_count > new_plan["daily_messages"]:
            raise HTTPException(status_code=400, detail="Over message quota")
        if (
            daily.token_count is not None
            and daily.token_count > new_plan["daily_tokens"]
        ):
            raise HTTPException(status_code=400, detail="Over token quota")
        if (
            daily.file_uploads is not None
            and daily.file_uploads > new_plan["max_file_uploads"]
        ):
            raise HTTPException(status_code=400, detail="Over file quota")

    charge_plan(str(current_user.user_id), plan)

    current_user.plan = plan
    db.commit()
    logger.info("Plan updated to %s for %s", plan, current_user.user_id)
    return success({"detail": "plan updated", "price": PLANS[plan]["price"]}).dict()
