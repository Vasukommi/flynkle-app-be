from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = "postgresql://postgres:postgres@postgres:5432/postgres"
    openai_api_key: str = ""

settings = Settings()
