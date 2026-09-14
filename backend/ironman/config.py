from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "IronMan"
    environment: str = "development"
    database_url: str = "sqlite:///./ironman.db"
    auth_mode: str = "development"
    single_user_id: str = "owner"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
