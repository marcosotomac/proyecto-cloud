from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Server Configuration
    NODE_ENV: str = "development"
    PORT: int = 8005

    # MongoDB Configuration
    MONGO_URI: str

    # JWT Configuration
    JWT_ACCESS_SECRET: str

    # Services URLs
    USERS_SERVICE_URL: str
    LLM_SERVICE_URL: str
    IMAGE_SERVICE_URL: str
    SPEECH_SERVICE_URL: str

    # S3 Configuration
    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
