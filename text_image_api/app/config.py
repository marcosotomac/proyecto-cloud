from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    port: int = 8000
    environment: str = "development"

    # S3/MinIO Configuration
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minio"
    s3_secret_key: str = "minio123"
    s3_region: str = "us-east-1"
    s3_bucket: str = "llmhist-image-dev"

    # Pollinations API
    pollinations_base_url: str = "https://image.pollinations.ai/prompt"

    # Analytics
    analytics_url: Optional[str] = None

    # Users Service
    users_service_url: str = "http://users-service:3000"

    # JWT Authentication
    # Debe coincidir con users service
    jwt_access_secret: str = "dev-super-secret-access-key-2024"

    class Config:
        env_file = ".env"


settings = Settings()
