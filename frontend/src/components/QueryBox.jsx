import { useState, useRef, useEffect } from "react";

const TICKERS = ["All", "AAPL", "MSFT", "NVDA"];

export default function QueryBox({ onSubmit, loading }) {
  const [question, setQuestion] = useState("");
  const [ticker, setTicker]     = useState("All");
  const textareaRef             = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 180) + "px";
  }, [question]);

  function handleSubmit(e) {
    e?.preventDefault();
    const q = question.trim();
    if (!q || loading) return;
    onSubmit({ question: q, ticker: ticker === "All" ? null : ticker });
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div className="query-box">
      <div className="query-inner">
        <div className="query-input-row">
          <textarea
            ref={textareaRef}
            className="query-textarea"
            placeholder="Ask anything about SEC filings — risks, revenue, strategy, competition…"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKey}
            rows={1}
            disabled={loading}
          />
        </div>

        <div className="query-controls">
          <div className="ticker-select-wrap">
            <label className="ticker-label">Scope</label>
            <div className="ticker-pills">
              {TICKERS.map((t) => (
                <button
                  key={t}
                  type="button"
                  className={`ticker-pill ${ticker === t ? "active" : ""}`}
                  onClick={() => setTicker(t)}
                  disabled={loading}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <button
            className={`submit-btn ${loading ? "submitting" : ""}`}
            onClick={handleSubmit}
            disabled={!question.trim() || loading}
            type="button"
          >
            {loading ? (
              <>
                <span className="spinner" />
                Analyzing…
              </>
            ) : (
              <>
                <span className="submit-icon">→</span>
                Ask FinSight
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
