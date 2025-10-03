"""Configuration management for Text-to-Speech API"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Environment
    environment: str = "development"
    log_level: str = "INFO"

    # S3 Configuration
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: str = "minio"
    s3_secret_key: str = "minio123"
    s3_bucket: str = "llmhist-tts-dev"
    s3_region: str = "us-east-1"

    # Users Service
    users_service_url: str = "http://users-service:3000"
    users_service_verify_url: str = "http://users-service:3000/auth/verify"

    # JWT
    jwt_public_key_path: str = "../jwt-public.key"
    # Debe coincidir con users service
    jwt_access_secret: str = "dev-super-secret-access-key-2024"

    # TTS Provider (gTTS - Google Text-to-Speech Free)
    tts_provider: str = "gtts"
    gtts_default_lang: str = "en"

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings"""
    return Settings()


settings = get_settings()
