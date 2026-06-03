from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import settings

app = FastAPI(title="FinSight API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


class QueryRequest(BaseModel):
    question: str
    ticker: str | None = None


@app.post("/query")
def query(req: QueryRequest):
    # TODO (Day 3+): route this through the agent loop.
    return {
        "question": req.question,
        "answer": "Agent not wired up yet — coming on Day 3.",
        "citations": [],
    }
