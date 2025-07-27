from datetime import date
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.database import get_db
from app.core import success, StandardResponse, PLANS
from app.services import upload_file_obj
from app.repositories import usage as usage_repo

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("", response_model=StandardResponse, summary="Upload file")
def upload_file(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = PLANS.get(current_user.plan, PLANS["free"])
    daily = usage_repo.get_daily_usage(db, current_user.user_id, date.today())
    uploads = daily.file_uploads if daily and daily.file_uploads is not None else 0
    if uploads >= plan.get("max_file_uploads", 0):
        raise HTTPException(status_code=403, detail="Upgrade required")

    url = upload_file_obj(file)
    usage_repo.increment_file_uploads(db, current_user.user_id, date.today())
    return success({"url": url}).dict()
