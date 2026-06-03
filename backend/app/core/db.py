import psycopg
from pgvector.psycopg import register_vector

from app.core.config import settings


def get_connection() -> psycopg.Connection:
    """Open a connection with the pgvector type adapter registered."""
    conn = psycopg.connect(settings.database_url)
    register_vector(conn)
    return conn


def init_db() -> None:
    """Create the vector extension, the chunks table, and an ANN index."""
    # The extension must exist before register_vector can find the type,
    # so create it on a plain connection first.
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS chunks (
                    id           BIGSERIAL PRIMARY KEY,
                    ticker       TEXT NOT NULL,
                    form_type    TEXT,
                    accession    TEXT,
                    chunk_index  INT,
                    content      TEXT NOT NULL,
                    embedding    vector({settings.embedding_dim})
                );
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS chunks_embedding_idx "
                "ON chunks USING hnsw (embedding vector_cosine_ops);"
            )
        conn.commit()