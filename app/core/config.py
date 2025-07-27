from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = "postgresql://postgres:postgres@postgres:5432/postgres"
    openai_api_key: str = ""
    secret_key: str = "secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    redis_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "uploads"

settings = Settings()
