# FinSight — SEC Filing Intelligence

> Ask a plain-English question about any major public company. FinSight retrieves evidence from SEC 10-K filings, fetches live market data, and returns a synthesized, source-cited answer — powered by a two-turn Gemini agent.

**Research and educational tool — not financial advice.**

Live demo: [finsight-sec.vercel.app](https://finsight-sec.vercel.app)

---

## System Architecture

```mermaid
graph TD
    User["User"] -->|question| FE["Frontend\nReact + Vite\nVercel"]
    FE -->|POST /query| BE["Backend\nFastAPI\nRender"]

    BE --> Agent["Agent Loop\ngemini-2.5-flash"]

    Agent -->|"Turn 1: routing\ncall search_filings?"| Router["Tool Router\nGemini decides\nwhich tools to call"]
    Agent -->|"Turn 2: synthesis\ncited prose answer"| Synth["Synthesizer\nGemini writes\nfinal answer"]

    Router -->|search_filings| Retriever["Retriever\npgvector cosine\ntop-k chunks"]
    Router -->|get_market_data| Market["Market Tool\nyfinance"]

    Retriever -->|vector search| DB[("Supabase\nPostgres + pgvector\n20 tickers · 2000+ chunks")]
    Market --> YF["Yahoo Finance"]

    Synth -->|answer + sources\n+ market_data| FE

    subgraph "Ingestion Pipeline (offline)"
        EDGAR["SEC EDGAR\n10-K Filings"] --> DL["sec-edgar-downloader\nDownload HTML"]
        DL --> Parse["BeautifulSoup\nExtract text"]
        Parse --> Chunk["Chunker\n4000 chars · 400 overlap\ncapped at 150 chunks"]
        Chunk --> Embed["gemini-embedding-001\n768-dim Matryoshka\nL2-normalized"]
        Embed --> DB
    end
```

---

## How It Works

A user question triggers a **two-turn Gemini interaction**:

1. **Turn 1 — Routing.** The agent sees the question and tool schemas. Gemini decides which tools to call: `search_filings` (RAG over SEC chunks), `get_market_data` (live yfinance), or both.

2. **Execution.** The selected tools run. `search_filings` runs a pgvector cosine similarity query against the chunks table and returns the top-k passages. `get_market_data` calls yfinance for price, P/E, market cap, and 52-week range.

3. **Turn 2 — Synthesis.** Gemini receives all tool results and writes a cited answer, referencing sources as `[Source N]` inline. The response includes the prose answer, source chunks, and market data cards.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, react-markdown |
| Styling | Custom CSS — Space Grotesk, JetBrains Mono, Inter |
| Backend | FastAPI (Python 3.12) |
| Agent / LLM | Google Gemini 2.5 Flash (google-genai SDK) |
| Embeddings | gemini-embedding-001, 768-dim (Matryoshka) |
| Vector DB | Supabase Postgres + pgvector (cosine similarity) |
| Market Data | yfinance |
| SEC Filings | sec-edgar-downloader |
| Frontend hosting | Vercel |
| Backend hosting | Render |
| Database hosting | Supabase |

---

## Coverage

20 S&P 500 companies across 5 sectors:

| Sector | Tickers |
|---|---|
| Technology | AAPL · MSFT · NVDA · GOOGL · META · AMZN |
| Finance | JPM · BAC · GS · MS |
| Healthcare | JNJ · PFE · UNH |
| Energy | XOM · CVX |
| Consumer | TSLA · WMT · KO · DIS · NFLX |

---

## Project Structure

```
Finsight/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── loop.py          # Two-turn Gemini agent
│   │   │   └── ticker.py        # Ticker name → symbol mapping
│   │   ├── core/
│   │   │   ├── config.py        # Settings (tickers, API keys, DB URL)
│   │   │   └── db.py            # Postgres connection
│   │   ├── ingestion/
│   │   │   └── ingest.py        # Download → chunk → embed → store
│   │   ├── retrieval/
│   │   │   └── retriever.py     # pgvector cosine similarity search
│   │   ├── tools/
│   │   │   └── market.py        # yfinance market data tool
│   │   └── main.py              # FastAPI app, /query endpoint
│   ├── tests/                   # Pytest test suite
│   ├── .env                     # Local env vars (not committed)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AnswerPanel.jsx  # Answer, sources, market data cards
│   │   │   └── QueryBox.jsx     # Search input + ticker selector
│   │   ├── App.jsx              # Root — query handler, cold start UX
│   │   ├── App.css
│   │   └── index.css            # Design system, CSS variables
│   ├── .env                     # VITE_API_URL (not committed)
│   └── package.json
└── README.md
```

---

## Local Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- A [Supabase](https://supabase.com) project with pgvector enabled
- A [Google AI Studio](https://aistudio.google.com) API key (free)

### 1 — Clone and configure backend

```powershell
git clone https://github.com/Jeetkavaiya/finsight.git
cd finsight\backend

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
GEMINI_API_KEY=your-google-ai-studio-key
SEC_EMAIL=your-email@example.com
```

> Use the **direct connection string** from Supabase → Settings → Database → Connection string (not the pooler). Port 5432.

### 2 — Initialize the database

```powershell
cd backend
python -c "from app.core.db import init_db; init_db()"
```

This creates the `chunks` table with a `vector(768)` column and a cosine similarity index.

### 3 — Run ingestion

```powershell
python -m app.ingestion.ingest
```

Downloads 10-K filings from SEC EDGAR, extracts text, chunks it, embeds with Gemini, and stores in Supabase. Skips tickers already in the database. Expect ~2–3 hours for all 20 tickers on the free tier due to Gemini rate limits (auto-retried with backoff).

> **Gemini free tier**: 1,000 embedding requests/day. If ingestion stops with `RESOURCE_EXHAUSTED`, wait for the daily quota to reset (midnight Pacific) and re-run — completed tickers are automatically skipped.

### 4 — Start the backend

```powershell
uvicorn app.main:app --reload --port 8000
```

Health check: `http://localhost:8000/health`
API docs: `http://localhost:8000/docs`

### 5 — Start the frontend

```powershell
cd ..\frontend
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

```powershell
npm install
npm run dev
```

Open `http://localhost:5173`

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | Supabase direct connection string (port 5432) |
| `GEMINI_API_KEY` | ✅ | Google AI Studio API key — used for both embeddings and LLM |
| `SEC_EMAIL` | ✅ | Contact email for SEC EDGAR User-Agent header |
| `SEC_COMPANY` | optional | Company name for SEC EDGAR header (default: `FinSight`) |

### Frontend (`frontend/.env`)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_URL` | ✅ | Backend URL — `http://localhost:8000` locally, Render URL in prod |

### Render (production backend)

| Variable | Value |
|---|---|
| `DATABASE_URL` | Supabase direct connection string |
| `GEMINI_API_KEY` | Google AI Studio key |
| `SEC_EMAIL` | Contact email |
| `VERCEL_URL` | `https://finsight-sec.vercel.app` (for CORS) |

---

## Deployment

### Backend → Render

1. Connect your GitHub repo to Render
2. Create a new **Web Service**
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add the environment variables above
6. Deploy

### Frontend → Vercel

1. Import the GitHub repo into Vercel
2. Set root directory to `frontend`
3. Add `VITE_API_URL` pointing to your Render service URL
4. Deploy

### Database → Supabase

1. Create a new Supabase project
2. Enable the pgvector extension: **Database → Extensions → vector**
3. Run the init script (step 2 in Local Setup above) to create the `chunks` table
4. Enable Row-Level Security: `ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;`
   - No policies needed — backend uses service role which bypasses RLS

---

## API Reference

### `POST /query`

Submit a question and receive a cited answer.

**Request:**
```json
{
  "question": "What risks did NVDA flag in their latest 10-K?",
  "ticker": "NVDA"
}
```

**Response:**
```json
{
  "answer": "NVIDIA flagged several key risks...[Source 1][Source 2]",
  "sources": [
    {
      "index": 1,
      "ticker": "NVDA",
      "chunk_index": 142,
      "score": 0.94,
      "snippet": "The semiconductor industry is highly competitive..."
    }
  ],
  "market_data": [
    {
      "ticker": "NVDA",
      "price": 875.39,
      "market_cap": "2.16T",
      "pe_trailing": 65.4,
      "52w_range": "$462 - $974"
    }
  ]
}
```

### `GET /health`

Returns `{"status": "ok"}`.

---

## Example Queries

```
What risks did NVDA flag in their latest 10-K?
What are Apple's main revenue segments?
How does Microsoft describe its cloud strategy?
What did JPMorgan say about interest rate risk?
How is Meta investing in AI infrastructure?
What competition risks does Tesla flag?
What does Alphabet say about AI regulation risks?
Compare Apple and Microsoft's R&D spending
```

---

## Known Limitations

- **Free-tier Gemini quota**: 1,000 embedding requests/day and ~750 query requests/day. Monitor at [ai.dev/rate-limit](https://ai.dev/rate-limit).
- **Render cold starts**: Backend sleeps after inactivity. First query after sleep takes 30–50s. The frontend shows a "waking up" banner after 5 seconds.
- **Data freshness**: Ingests the most recent 10-K available on SEC EDGAR at time of ingestion. Filings are not automatically refreshed.
- **Chunk cap**: Each company is capped at 150 chunks to stay within daily quota during ingestion. Very large filings (e.g. JPMorgan at 410 raw chunks) are truncated.

---

## License

MIT
