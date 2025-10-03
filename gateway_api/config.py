from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Server Configuration
    NODE_ENV: str = "development"
    PORT: int = 8080

    # JWT Configuration
    JWT_ACCESS_SECRET: str

    # Services URLs
    USERS_SERVICE_URL: str
    LLM_SERVICE_URL: str
    IMAGE_SERVICE_URL: str
    SPEECH_SERVICE_URL: str
    ANALYTICS_SERVICE_URL: str

    # Gateway Configuration
    ENABLE_RATE_LIMIT: bool = True
    RATE_LIMIT_WINDOW_MS: int = 60000
    RATE_LIMIT_MAX_REQUESTS: int = 100

    # CORS Configuration
    CORS_ORIGINS: str = "*"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Analytics Tracking
    ENABLE_ANALYTICS: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
