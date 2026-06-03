<<<<<<< HEAD
# FinSight — Agentic Financial Research Assistant

Ask a plain-English question about a public company; FinSight's agent gathers
evidence from SEC filings and live market data and returns a synthesized,
source-cited answer.

> Research/educational tool — not financial advice.

## Stack
- Backend: FastAPI (Python 3.12)
- Agent/RAG: LlamaIndex or LangChain (tool-calling)
- Data store: Postgres + pgvector (Supabase in prod)
- Frontend: React + Tailwind (Vercel in prod)
- Hosting: Render (backend), Vercel (frontend), Supabase (db)

## Local setup
```bash
# 1. backend env
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. run the API
uvicorn app.main:app --reload

# 3. visit http://localhost:8000/health  and  http://localhost:8000/docs
```

Or run everything (API + pgvector db) with Docker:
```bash
cp .env.example .env
docker compose up --build
```

## Tests
```bash
cd backend && pytest
```
=======
# Finsight
>>>>>>> 3e2975e3b503a4de6d4d8fb0b735d31e1bb4a38f
