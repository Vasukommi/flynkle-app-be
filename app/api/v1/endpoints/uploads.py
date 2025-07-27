from datetime import date
from uuid import UUID
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.database import get_db
from app.core import success, StandardResponse, PLANS, settings
from app.services import upload_file_obj, get_file_url, delete_file
from app.repositories import usage as usage_repo
from app.repositories import upload as upload_repo
from app.schemas import UploadRead

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = {"image/png", "image/jpeg", "text/plain", "application/pdf"}

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

    data = file.file.read()
    size = len(data)
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    file.file.seek(0)
    key, size = upload_file_obj(file)
    record = upload_repo.create_upload(
        db,
        current_user.user_id,
        settings.minio_bucket,
        key,
        file.content_type,
        size,
    )
    url = get_file_url(key)
    usage_repo.increment_file_uploads(db, current_user.user_id, date.today())
    payload = {"url": url, "upload_id": record.upload_id}
    return success(payload).dict()


@router.get("", response_model=StandardResponse, summary="List uploads")
def list_uploads(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> list[UploadRead]:
    uploads = upload_repo.list_uploads(db, current_user.user_id, skip=skip, limit=limit)
    payload = [
        UploadRead.model_validate(u).model_copy(update={"url": get_file_url(u.key)})
        for u in uploads
    ]
    return success(payload).dict()


@router.delete("/{upload_id}", response_model=StandardResponse, summary="Delete upload")
def delete_upload(
    upload_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    upload = upload_repo.get_upload(db, upload_id)
    if not upload or upload.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="File not found")
    delete_file(upload.key)
    upload_repo.delete_upload(db, upload)
    return success({"deleted": str(upload_id)}).dict()
