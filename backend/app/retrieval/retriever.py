import math
from google import genai
from google.genai import types
from app.core.config import settings
from app.core.db import get_connection

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.llm_api_key)
    return _client

def _normalize(vector: list[float]) -> list[float]:
    """L2-normalize a vector. Required for truncated Gemini embeddings (<3072 dims)."""
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]


def retrieve(question: str, top_k: int = 5, ticker: str | None = None) -> list[dict]:
    """
    Embed the question with RETRIEVAL_QUERY task type, then run a cosine
    similarity search against the chunks table.

    Args:
        question: Natural-language question from the user.
        top_k:    Number of chunks to return.
        ticker:   Optional ticker filter (e.g. "NVDA"). If None, searches all tickers.

    Returns:
        List of dicts with keys: ticker, chunk_index, content, score (0–1).
    """
    # Embed the query — MUST use RETRIEVAL_QUERY here (not RETRIEVAL_DOCUMENT)
    resp = client.models.embed_content(
        model=settings.embedding_model,
        contents=[question],
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=settings.embedding_dim,
        ),
    )
    q_emb = _normalize(resp.embeddings[0].values)

    with get_connection() as conn:
        with conn.cursor() as cur:
            if ticker:
                cur.execute(
                    """
                    SELECT ticker, chunk_index, content,
                           embedding <=> %s::vector AS distance
                    FROM chunks
                    WHERE ticker = %s
                    ORDER BY distance
                    LIMIT %s
                    """,
                    (q_emb, ticker.upper(), top_k),
                )
            else:
                cur.execute(
                    """
                    SELECT ticker, chunk_index, content,
                           embedding <=> %s::vector AS distance
                    FROM chunks
                    ORDER BY distance
                    LIMIT %s
                    """,
                    (q_emb, top_k),
                )
            rows = cur.fetchall()

    return [
        {
            "ticker": r[0],
            "chunk_index": r[1],
            "content": r[2],
            "score": round(1 - r[3], 4),  # cosine similarity (higher = more relevant)
        }
        for r in rows
    ]