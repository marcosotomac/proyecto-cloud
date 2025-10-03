from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    NODE_ENV: str = "development"
    PORT: int = 8002
    MONGO_URI: str = "mongodb://mongo:27017/llm_chat"
    MONGO_DB_NAME: str = "llm_chat"
    GITHUB_TOKEN: str
    GITHUB_API_BASE: str = "https://models.inference.ai.azure.com"
    GITHUB_DEFAULT_MODEL: str = "gpt-4o-mini"
    JWT_ACCESS_SECRET: str = "dev-super-secret-access-key-2024"
    USERS_SERVICE_URL: str = "http://users-service:3000"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
