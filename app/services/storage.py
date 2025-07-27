from uuid import uuid4
import io
from minio import Minio
from app.core import settings

client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=False,
)


def upload_file_obj(file_obj) -> tuple[str, int]:
    """Upload a file and return its key and size."""
    bucket = settings.minio_bucket
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    data = file_obj.file.read()
    size = len(data)
    key = f"{uuid4()}-{file_obj.filename}"
    client.put_object(
        bucket,
        key,
        io.BytesIO(data),
        length=size,
        content_type=file_obj.content_type,
    )
    return key, size


def get_file_url(key: str, expires: int = 3600) -> str:
    """Return a presigned URL for accessing the file."""
    bucket = settings.minio_bucket
    return client.presigned_get_object(bucket, key, expires=expires)


def delete_file(key: str) -> None:
    bucket = settings.minio_bucket
    client.remove_object(bucket, key)

