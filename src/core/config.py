from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/workflows.db"
    redis_url: str = "redis://localhost:6379/0"
    cloud_provider: str = "local"
    aws_region: str = "us-east-1"
    azure_region: str = "eastus"
    llm_provider: str = "mock"
    log_level: str = "INFO"
    workflow_max_retries: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()
