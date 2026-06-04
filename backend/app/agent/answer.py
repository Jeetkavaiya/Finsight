from google import genai
from app.core.config import settings

client = genai.Client(api_key=settings.llm_api_key)

SYSTEM_PROMPT = """\
You are FinSight, a financial research assistant. Your job is to answer questions \
about SEC filings accurately and concisely.

Rules:
- Answer using ONLY the sources provided below. Do not use prior knowledge.
- Cite every factual claim with [Source N] immediately after the claim.
- If multiple sources support a claim, cite all of them: [Source 1][Source 3].
- If the sources do not contain enough information to answer, say so explicitly.
- Keep the answer focused. Do not pad with filler.
"""


def answer(question: str, chunks: list[dict]) -> dict:
    """
    Build a cited answer from retrieved chunks using Gemini.

    Args:
        question: The original user question.
        chunks:   List of chunk dicts from retrieve() — must have ticker + content.

    Returns:
        Dict with keys:
          - answer (str): Cited prose answer.
          - sources (list[dict]): The chunks passed in, for frontend rendering.
    """
    if not chunks:
        return {
            "answer": "I couldn't find relevant information in the available filings.",
            "sources": [],
        }

    # Build the source block
    source_block = "\n\n".join(
        f"[Source {i + 1} | {c['ticker']} chunk {c['chunk_index']} | relevance {c['score']}]\n{c['content']}"
        for i, c in enumerate(chunks)
    )

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Sources:\n{source_block}\n\n"
        f"Question: {question}"
    )

    resp = client.models.generate_content(
        model=settings.llm_model,
        contents=prompt,
    )

    return {
        "answer": resp.text,
        "sources": [
            {
                "index": i + 1,
                "ticker": c["ticker"],
                "chunk_index": c["chunk_index"],
                "score": c["score"],
                # Truncate content for the API response — full text is in the DB
                "snippet": c["content"][:400] + ("…" if len(c["content"]) > 400 else ""),
            }
            for i, c in enumerate(chunks)
        ],
    }