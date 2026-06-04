from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.retrieval.retriever import retrieve
from app.agent.answer import answer

app = FastAPI(title="FinSight API", version="0.3.0")

# Request / response models

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=5, description="Natural-language question about SEC filings")
    ticker: str | None = Field(None, description="Optional: restrict search to one ticker (AAPL, MSFT, NVDA)")
    top_k: int = Field(5, ge=1, le=20, description="Number of source chunks to retrieve")


class SourceItem(BaseModel):
    index: int
    ticker: str
    chunk_index: int
    score: float
    snippet: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceItem]

# Routes

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    try:
        chunks = retrieve(req.question, top_k=req.top_k, ticker=req.ticker)
        return answer(req.question, chunks)
    except Exception as exc:
        # Surface errors clearly during development
        raise HTTPException(status_code=500, detail=str(exc))