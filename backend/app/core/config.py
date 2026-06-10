from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://finsight:finsight@localhost:5432/finsight"

    llm_api_key: str = ""
    llm_model: str = "gemini-2.5-flash"

    embedding_model: str = "gemini-embedding-001"
    embedding_dim: int = 768

    sec_company: str = "FinSight"
    sec_email: str = "your-email@example.com"

    tickers: list[str] = [
        "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN",
        "JPM", "BAC", "GS", "MS",
        "JNJ", "PFE", "UNH",
        "XOM", "CVX",
        "TSLA", "WMT", "KO", "DIS", "NFLX",
    ]

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