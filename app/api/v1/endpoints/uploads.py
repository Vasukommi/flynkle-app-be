from fastapi import APIRouter, UploadFile, File, Depends
from app.api.deps import get_current_user
from app.core import success, StandardResponse
from app.services import upload_file_obj

router = APIRouter(prefix="/uploads", tags=["uploads"])

@router.post("", response_model=StandardResponse, summary="Upload file")
def upload_file(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    url = upload_file_obj(file)
    return success({"url": url}).dict()

