import { useState } from "react";
import AnswerPanel from "./components/AnswerPanel";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const ALL_TICKERS = [
  "AAPL","MSFT","NVDA","GOOGL","META","AMZN",
  "JPM","BAC","GS","MS","JNJ","PFE","UNH",
  "XOM","CVX","TSLA","WMT","KO","DIS","NFLX",
];

const QUICK_CHIPS = [
  { label: "NVDA risk factors",       ticker: "NVDA", q: "What risks did NVDA flag in their latest 10-K?" },
  { label: "AAPL revenue breakdown",  ticker: "AAPL", q: "What are Apple's main revenue segments?" },
  { label: "JPM interest rate",       ticker: "JPM",  q: "What did JPMorgan say about interest rate risk?" },
  { label: "TSLA competition",        ticker: "TSLA", q: "What competition risks does Tesla flag?" },
  { label: "META AI strategy",        ticker: "META", q: "How is Meta investing in AI infrastructure?" },
];

const SAMPLE_QUESTIONS = [
  { ticker: "NVDA", text: "What risks did NVDA flag in their latest 10-K?" },
  { ticker: "AAPL", text: "What are Apple's main revenue segments?" },
  { ticker: "MSFT", text: "How does Microsoft describe its cloud strategy?" },
  { ticker: "GOOGL", text: "What does Alphabet say about AI regulation risks?" },
  { ticker: "META", text: "How is Meta investing in AI infrastructure?" },
  { ticker: "JPM",  text: "What did JPMorgan say about interest rate risk?" },
  { ticker: "TSLA", text: "What competition risks does Tesla flag?" },
  { ticker: "AMZN", text: "How does Amazon describe AWS growth drivers?" },
];

export default function App() {
  const [question, setQuestion]     = useState("");
  const [result, setResult]         = useState(null);
  const [loading, setLoading]       = useState(false);
  const [isSlowLoad, setIsSlowLoad] = useState(false);
  const [error, setError]           = useState(null);
  const [lastQuery, setLastQuery]   = useState("");

  async function handleQuery({ question: q, ticker }) {
    const trimmed = q.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setIsSlowLoad(false);
    setError(null);
    setResult(null);
    setLastQuery(trimmed);

    const slowTimer   = setTimeout(() => setIsSlowLoad(true), 5000);
    const controller  = new AbortController();
    const hardTimeout = setTimeout(() => controller.abort(), 60000);

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed, ticker_hint: ticker || null }),
        signal: controller.signal,
      });
      clearTimeout(hardTimeout);
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Server error ${res.status}: ${text}`);
      }
      setResult(await res.json());
    } catch (err) {
      if (err.name === "AbortError") {
        setError("Request timed out. The server may be starting up — please try again.");
      } else {
        setError(err.message);
      }
    } finally {
      clearTimeout(slowTimer);
      clearTimeout(hardTimeout);
      setLoading(false);
      setIsSlowLoad(false);
    }
  }

  function submitCurrent() {
    handleQuery({ question, ticker: null });
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitCurrent();
    }
  }

  const showResults = loading || result || error;

  return (
    <div className="app">
      {/* ── Nav ── */}
      <nav className="app-nav">
        <div className="nav-logo">
          <div className="logo-mark">FS</div>
          <span className="logo-name">Fin<em>Sight</em></span>
        </div>
        <div className="nav-right">
          <div className="nav-badge">
            <b>●</b> 20 companies live
          </div>
          <a
            href="https://github.com/Jeetkavaiya/Finsight"
            className="nav-link"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="hero">
        <p className="eyebrow">SEC Filing Intelligence</p>
        <h1 className="hero-title">
          Ask anything about<br />
          <em>public companies</em>
        </h1>
        <p className="hero-sub">
          Source-cited answers from SEC 10-K filings
          <span>·</span>
          Live market data
          <span>·</span>
          20 S&amp;P 500 companies
        </p>

        {/* Search box */}
        <div className="search-box">
          <input
            className="search-input"
            type="text"
            placeholder="What risks did NVDA flag in their latest 10-K?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKey}
            disabled={loading}
          />
          <button
            className="search-btn"
            onClick={submitCurrent}
            disabled={!question.trim() || loading}
          >
            {loading ? <span className="spinner" /> : "Analyze →"}
          </button>
        </div>

        {/* Quick filter chips */}
        <div className="quick-chips">
          {QUICK_CHIPS.map((c) => (
            <button
              key={c.label}
              className="quick-chip"
              onClick={() => {
                setQuestion(c.q);
                handleQuery({ question: c.q, ticker: c.ticker });
              }}
              disabled={loading}
            >
              <b>{c.ticker}</b>&nbsp;{c.label.replace(c.ticker + " ", "")}
            </button>
          ))}
        </div>

        {/* All 20 ticker pills */}
        <div className="ticker-pills-row">
          {ALL_TICKERS.map((t) => (
            <span key={t} className="ticker-pill-sm">{t}</span>
          ))}
        </div>
      </section>

      {/* ── Main content ── */}
      <main className="app-main">
        {/* Slow load banner */}
        {loading && isSlowLoad && (
          <div className="info-banner">
            <span>⏳</span>
            <span>Server is waking up from sleep mode — this may take 30–50s…</span>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="error-banner">
            <span>⚠</span>
            <span>{error}</span>
          </div>
        )}

        {/* Results */}
        {showResults && (
          <AnswerPanel result={result} loading={loading} question={lastQuery} />
        )}

        {/* Empty state — sample questions */}
        {!loading && !result && !error && (
          <div className="empty-state">
            <div className="empty-grid">
              {SAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q.text}
                  className="sample-card"
                  onClick={() => {
                    setQuestion(q.text);
                    handleQuery({ question: q.text, ticker: q.ticker });
                  }}
                >
                  <span className="sample-ticker">{q.ticker}</span>
                  <span className="sample-text">{q.text}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <span>Powered by Gemini 2.5 Flash · SEC EDGAR · yfinance</span>
      </footer>
    </div>
  );
}