import { useState } from "react";
import QueryBox from "./components/QueryBox";
import AnswerPanel from "./components/AnswerPanel";
import "./App.css";

const API_BASE = "http://localhost:8000";

export default function App() {
  const [result, setResult]     = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const [lastQuery, setLastQuery] = useState("");

  async function handleQuery({ question, ticker }) {
    setLoading(true);
    setError(null);
    setResult(null);
    setLastQuery(question);

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          ticker_hint: ticker || null,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Server error ${res.status}: ${text}`);
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
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
          {["AAPL", "MSFT", "NVDA"].map((t) => (
            <span key={t} className="ticker-chip">{t}</span>
          ))}
        </div>
      </header>

      <main className="app-main">
        <QueryBox onSubmit={handleQuery} loading={loading} />

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
        <span>Powered by Gemini 2.5 Flash · SEC EDGAR · yfinance</span>
      </footer>
    </div>
  );
}

const SAMPLE_QUESTIONS = [
  { ticker: "NVDA", text: "What risks did NVDA flag in their latest 10-K?" },
  { ticker: "AAPL", text: "What are Apple's main revenue segments?" },
  { ticker: "MSFT", text: "How does Microsoft describe its cloud strategy?" },
  { ticker: "NVDA", text: "What does NVDA say about AI chip competition?" },
  { ticker: "AAPL", text: "What liquidity risks does Apple mention?" },
  { ticker: "MSFT", text: "What are Microsoft's biggest operating expenses?" },
];
