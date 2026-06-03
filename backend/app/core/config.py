from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://finsight:finsight@localhost:5432/finsight"

    # Google AI Studio key (free, no credit card). Powers BOTH embeddings
    # and the agent. Get it at https://aistudio.google.com -> "Get API key".
    llm_api_key: str = ""
    llm_model: str = "gemini-2.5-flash"

    # Embeddings. gemini-embedding-001 defaults to 3072 dims; we reduce to 768
    # (Matryoshka) so pgvector can index it — pgvector ANN indexes cap at 2000.
    embedding_model: str = "gemini-embedding-001"
    embedding_dim: int = 768

    # SEC EDGAR REQUIRES a real contact email in its User-Agent header.
    # Set sec_email in .env or SEC will throttle/block you.
    sec_company: str = "FinSight"
    sec_email: str = "your-email@example.com"

    # Companies to ingest on Day 2.
    tickers: list[str] = ["AAPL", "MSFT", "NVDA"]

    # External APIs (Day 5).
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