import math
import time
import warnings
from pathlib import Path

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from sec_edgar_downloader import Downloader

from app.core.config import settings
from app.core.db import get_connection, init_db

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

client = genai.Client(api_key=settings.llm_api_key)

DOWNLOAD_DIR = Path("data/edgar")

EMBED_BATCH_SIZE = 5
EMBED_SLEEP_SECONDS = 4


def fetch_filings(ticker: str, form_type: str = "10-K", limit: int = 1) -> list[Path]:
    """Download filings for a ticker; return paths to each primary document."""
    dl = Downloader(settings.sec_company, settings.sec_email, str(DOWNLOAD_DIR))
    dl.get(form_type, ticker, limit=limit, download_details=True)

    base = DOWNLOAD_DIR / "sec-edgar-filings" / ticker / form_type
    if not base.exists():
        return []

    docs: list[Path] = []
    for accession_dir in sorted(base.iterdir()):
        doc = _primary_doc(accession_dir)
        if doc:
            docs.append(doc)
    return docs


def _primary_doc(accession_dir: Path) -> Path | None:
    """Prefer the largest HTML file (the primary doc); fall back to raw submission."""
    htmls = sorted(accession_dir.glob("*.htm*"))
    if htmls:
        return max(htmls, key=lambda p: p.stat().st_size)
    full = accession_dir / "full-submission.txt"
    return full if full.exists() else None


def extract_text(path: Path) -> str:
    """Strip HTML to readable text and drop blank lines."""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(raw, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = (ln.strip() for ln in text.splitlines())
    return "\n".join(ln for ln in lines if ln)


def chunk_text(text: str, max_chars: int = 4000, overlap: int = 400) -> list[str]:
    """Greedily pack paragraphs into ~max_chars chunks with a small overlap."""
    paragraphs = [p for p in text.split("\n") if p]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 1 <= max_chars:
            current = f"{current}\n{para}" if current else para
        else:
            if current:
                chunks.append(current)
            tail = current[-overlap:] if current else ""
            current = f"{tail}\n{para}" if tail else para
    if current:
        chunks.append(current)
    return chunks


def _normalize(vector: list[float]) -> list[float]:
    """L2-normalize. Gemini embeddings reduced below 3072 dims aren't
    normalized, so we do it ourselves for correct cosine similarity."""
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]


def _embed_batch(texts: list[str], max_retries: int = 3) -> list[list[float]]:
    """Embed one small batch, waiting and retrying if we hit a rate limit (429)."""
    for attempt in range(max_retries):
        try:
            response = client.models.embed_content(
                model=settings.embedding_model,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=settings.embedding_dim,
                ),
            )
            return [_normalize(e.values) for e in response.embeddings]
        except ClientError as exc:
            if exc.code == 429 and attempt < max_retries - 1:
                wait = 30 * (attempt + 1)
                print(f"    rate limited — waiting {wait}s, then retrying ...")
                time.sleep(wait)
                continue
            raise
    return []


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed all chunks in small, paced batches to respect free-tier limits."""
    embeddings: list[list[float]] = []
    for start in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[start:start + EMBED_BATCH_SIZE]
        embeddings.extend(_embed_batch(batch))
        print(f"    embedded {len(embeddings)}/{len(texts)} chunks")
        time.sleep(EMBED_SLEEP_SECONDS)
    return embeddings


def store_chunks(conn, ticker, form_type, accession, chunks, embeddings) -> None:
    with conn.cursor() as cur:
        for i, (content, embedding) in enumerate(zip(chunks, embeddings)):
            cur.execute(
                "INSERT INTO chunks "
                "(ticker, form_type, accession, chunk_index, content, embedding) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (ticker, form_type, accession, i, content, embedding),
            )
    conn.commit()


def is_ingested(ticker: str) -> int:
    """Return chunk count for ticker using a fresh short-lived connection."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM chunks WHERE ticker = %s", (ticker,))
            return cur.fetchone()[0]


def main() -> None:
    init_db()
    form_type = "10-K"

    for ticker in settings.tickers:
        # Fresh connection for the skip check avoids stale connection issues
        count = is_ingested(ticker)
        if count > 0:
            print(f"  skipping {ticker} — {count} chunks already in DB")
            continue

        print(f"Fetching {form_type} for {ticker} ...")
        docs = fetch_filings(ticker, form_type, limit=1)
        if not docs:
            print(f"  no filing found for {ticker}")
            continue

        for doc in docs:
            accession = doc.parent.name
            chunks = chunk_text(extract_text(doc))[:150]
            print(f"  {ticker}: {len(chunks)} chunks — embedding ...")

            # Embedding can take 10-20 minutes per ticker on free tier.
            # Open a FRESH connection only after embedding is done to avoid
            # Postgres dropping the idle connection mid-run.
            embeddings = embed_texts(chunks)

            with get_connection() as conn:
                store_chunks(conn, ticker, form_type, accession, chunks, embeddings)
            print(f"  stored {len(chunks)} chunks for {ticker}")

    print("Ingestion complete.")


if __name__ == "__main__":
    main()