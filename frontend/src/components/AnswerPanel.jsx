import { useState } from "react";
import ReactMarkdown from "react-markdown";

/* ── Market data section (full-width row below the 2-col grid) ── */
function MarketSection({ items }) {
  if (!items || items.length === 0) return null;

  // Build display cards from the first item (single-ticker queries)
  // or show one card per ticker for multi-ticker queries
  return (
    <div className="market-section">
      <div className="market-section-title">
        Live Market Data · {items.map((m) => m.ticker).join(", ")}
      </div>
      <div className="market-grid">
        {items.map((m, i) =>
          m.error ? (
            <div key={i} className="market-card">
              <div className="market-card-label">{m.ticker ?? "—"}</div>
              <div className="market-card-value" style={{ fontSize: 13, color: "var(--red)" }}>
                {m.error}
              </div>
            </div>
          ) : (
            <MarketCard key={i} data={m} />
          )
        )}
      </div>
    </div>
  );
}

function MarketCard({ data }) {
  const price = data.price ? `$${Number(data.price).toFixed(2)}` : null;
  const cap   = data.market_cap ?? null;
  const pe    = data.pe_trailing ?? data.pe_forward ?? null;
  const range = data["52w_range"] ?? data["52_week_range"] ?? null;

  return (
    <>
      {price && (
        <div className="market-card">
          <div className="market-card-label">Price</div>
          <div className="market-card-value">{price}</div>
          <div className="market-card-sub">{data.ticker}</div>
        </div>
      )}
      {cap && (
        <div className="market-card">
          <div className="market-card-label">Market Cap</div>
          <div className="market-card-value" style={{ fontSize: 16 }}>{cap}</div>
          <div className="market-card-sub">&nbsp;</div>
        </div>
      )}
      {pe && (
        <div className="market-card">
          <div className="market-card-label">P/E Ratio</div>
          <div className="market-card-value">{pe}×</div>
          <div className="market-card-sub">trailing</div>
        </div>
      )}
      {range && (
        <div className="market-card">
          <div className="market-card-label">52-Week Range</div>
          <div className="market-card-value" style={{ fontSize: 15 }}>{range}</div>
          <div className="market-card-sub">&nbsp;</div>
        </div>
      )}
    </>
  );
}

/* ── Source card (sidebar) ── */
function SourceCard({ source, index }) {
  const [open, setOpen] = useState(false);
  const num = source.index ?? index + 1;
  const score = source.score ? Math.round(source.score * 100) : null;

  return (
    <div className={`source-card ${open ? "open" : ""}`}>
      <button className="source-header-btn" onClick={() => setOpen(!open)}>
        <div className="source-meta">
          <span className="source-num">S{num}</span>
          <span className="source-ticker-badge">{source.ticker}</span>
          {score != null && <span className="source-score">{score}%</span>}
        </div>
        <span className={`chevron ${open ? "up" : "down"}`}>›</span>
      </button>
      {open && (
        <div className="source-body">
          <p className="source-snippet">{source.snippet}</p>
          <div className="source-form-row">
            <span className="source-form-tag">10-K</span>
            {source.chunk_index != null && (
              <span className="source-form-tag">chunk {source.chunk_index}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Skeleton loader ── */
function LoadingState() {
  return (
    <div className="loading-state">
      <div className="loading-ring" />
      <p className="loading-text">Analyzing SEC filings…</p>
      <p className="loading-sub">Retrieving relevant passages</p>
    </div>
  );
}

/* ── Main export ── */
export default function AnswerPanel({ result, loading, question }) {
  if (loading) return <LoadingState />;
  if (!result) return null;

  const { answer, sources = [], market_data = [] } = result;

  // Detect ticker from sources for the badge
  const detectedTicker = sources[0]?.ticker ?? null;

  return (
    <div className="answer-panel">
      {/* Query echo bar */}
      <div className="query-bar">
        <span className="query-bar-label">Query</span>
        <span className="query-bar-text">{question}</span>
        {detectedTicker && (
          <span className="ticker-badge">{detectedTicker}</span>
        )}
      </div>

      {/* 2-column results grid */}
      <div className="results-grid">
        {/* Left — AI answer */}
        <div className="answer-box">
          <div className="answer-box-head">
            <span className="answer-box-label">AI Answer</span>
            <span className="answer-box-model">gemini-2.5-flash</span>
          </div>
          <div className="answer-body">
            <ReactMarkdown>{answer}</ReactMarkdown>
          </div>
        </div>

        {/* Right — Sources sidebar */}
        {sources.length > 0 && (
          <div className="sources-panel">
            <div className="sources-header">
              Sources · {sources.length} passage{sources.length !== 1 ? "s" : ""}
            </div>
            {sources.map((s, i) => (
              <SourceCard key={i} source={s} index={i} />
            ))}
          </div>
        )}

        {/* Market data — spans full width */}
        {market_data.length > 0 && (
          <MarketSection items={market_data} />
        )}
      </div>
    </div>
  );
}