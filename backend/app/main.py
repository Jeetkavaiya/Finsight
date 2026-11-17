from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.agent.loop import run
from app.core.db import get_connection
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="FinSight API", version="0.4.0")

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:4173",
]
VERCEL_URL = os.getenv("VERCEL_URL", "")
if VERCEL_URL:
    ALLOWED_ORIGINS.append(VERCEL_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request / response models
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=5, description="Natural-language question about SEC filings or market data")
    ticker: str | None = Field(None, description="Optional: hint the agent toward one ticker (AAPL, MSFT, NVDA)")
    top_k: int = Field(5, ge=1, le=10, description="Number of filing chunks to retrieve")


class SourceItem(BaseModel):
    index: int
    ticker: str
    chunk_index: int
    score: float
    snippet: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    market_data: list[dict]

# Routes
@app.get("/health")
def health():
    return {"status": "ok", "version": "0.4.0"}


@app.get("/db-ping")
def db_ping():
    """Run a real query against Supabase without touching Gemini.

    Used by the keep-alive workflow so the free-tier project registers
    database activity even when the LLM API is down or rate-limited.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM chunks;")
                (count,) = cur.fetchone()
        return {"status": "ok", "chunks": count}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unreachable: {exc}")


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    try:
        return run(question=req.question, ticker_hint=req.ticker)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))