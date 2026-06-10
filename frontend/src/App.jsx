import { useState } from "react";
import QueryBox from "./components/QueryBox";
import AnswerPanel from "./components/AnswerPanel";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [result, setResult]       = useState(null);
  const [loading, setLoading]     = useState(false);
  const [isSlowLoad, setIsSlowLoad] = useState(false);
  const [error, setError]         = useState(null);
  const [lastQuery, setLastQuery] = useState("");

  async function handleQuery({ question, ticker }) {
    setLoading(true);
    setIsSlowLoad(false);
    setError(null);
    setResult(null);
    setLastQuery(question);

    const slowTimer = setTimeout(() => setIsSlowLoad(true), 5000);

    const controller = new AbortController();
    const hardTimeout = setTimeout(() => controller.abort(), 60000);

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, ticker_hint: ticker || null }),
        signal: controller.signal,
      });
      clearTimeout(hardTimeout);

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Server error ${res.status}: ${text}`);
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      if (err.name === "AbortError") {
        setError("Request timed out. The server may be starting up — please try again in a moment.");
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

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo-row">
          <span className="logo-mark">FS</span>
          <div>
            <h1 className="logo-title">FinSight</h1>
            <p className="logo-sub">SEC Filing Intelligence</p>
          </div>
        </div>
        <div className="header-chips">
          {["AAPL", "MSFT", "NVDA", "GOOGL", "META", "JPM", "TSLA"].map((t) => (
            <span key={t} className="ticker-chip">{t}</span>
          ))}
        </div>
      </header>

      <main className="app-main">
        <QueryBox onSubmit={handleQuery} loading={loading} />

        {loading && isSlowLoad && (
          <div className="error-banner" style={{ background: "rgba(75,150,232,0.08)", borderColor: "rgba(75,150,232,0.2)", color: "var(--text-muted)" }}>
            <span className="error-icon">⏳</span>
            <span>Server is waking up from sleep mode — this may take 30–50s…</span>
          </div>
        )}

        {error && (
          <div className="error-banner">
            <span className="error-icon">⚠</span>
            <span>{error}</span>
          </div>
        )}

        {(loading || result) && (
          <AnswerPanel
            result={result}
            loading={loading}
            question={lastQuery}
          />
        )}

        {!loading && !result && !error && (
          <div className="empty-state">
            <div className="empty-grid">
              {SAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q.text}
                  className="sample-card"
                  onClick={() => handleQuery({ question: q.text, ticker: q.ticker })}
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
        <span>Powered by Gemini 2.5 Flash · SEC EDGAR · 20 S&P 500 companies</span>
      </footer>
    </div>
  );
}

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