from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.agent.loop import run
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FinSight API", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
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


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    try:
        return run(question=req.question, ticker_hint=req.ticker)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))