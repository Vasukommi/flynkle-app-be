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


def upload_file_obj(file_obj) -> str:
    """Upload a file and return its public URL."""
    bucket = settings.minio_bucket
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    data = file_obj.file.read()
    key = f"{uuid4()}-{file_obj.filename}"
    client.put_object(bucket, key, io.BytesIO(data), length=len(data), content_type=file_obj.content_type)
    return f"http://{settings.minio_endpoint}/{bucket}/{key}"

