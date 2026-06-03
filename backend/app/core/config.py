from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://finsight:finsight@localhost:5432/finsight"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    financial_api_key: str = ""
    news_api_key: str = ""
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
