import { useState } from "react";

// ─── helpers ────────────────────────────────────────────────────────────────

/** Parse inline [Source N] markers into React spans with highlighted chips */
function parseAnswer(text) {
  if (!text) return null;
  // Split on [Source N] or [Source N, M, ...] patterns
  const parts = text.split(/(\[Source\s[\d,\s]+\])/gi);
  return parts.map((part, i) => {
    if (/^\[Source/i.test(part)) {
      return (
        <cite key={i} className="source-inline">
          {part}
        </cite>
      );
    }
    return part;
  });
}

// ─── Sub-components ─────────────────────────────────────────────────────────

function SkeletonLoader() {
  return (
    <div className="skeleton-wrap">
      <div className="skeleton-bar w-90" />
      <div className="skeleton-bar w-75" />
      <div className="skeleton-bar w-85" />
      <div className="skeleton-bar w-60" />
      <div className="skeleton-spacer" />
      <div className="skeleton-bar w-40" />
    </div>
  );
}

function MarketDataBlock({ items }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="market-block">
      <h3 className="block-title">
        <span className="block-icon">◈</span> Live Market Data
      </h3>
      <div className="market-cards">
        {items.map((m, i) => (
          <MarketCard key={i} data={m} />
        ))}
      </div>
    </div>
  );
}

function MarketCard({ data }) {
  if (data.error) {
    return (
      <div className="market-card error-card">
        <span className="market-ticker">{data.ticker || "—"}</span>
        <span className="market-error">{data.error}</span>
      </div>
    );
  }

  const rows = [
    { label: "Price",        value: data.price        ? `$${Number(data.price).toFixed(2)}` : "—" },
    { label: "Mkt Cap",      value: data.market_cap   ?? "—" },
    { label: "P/E (trail)",  value: data.pe_trailing  ?? "—" },
    { label: "P/E (fwd)",    value: data.pe_forward   ?? "—" },
    { label: "52W Range",    value: data["52w_range"] ?? data["52_week_range"] ?? "—" },
    { label: "Rev TTM",      value: data.revenue_ttm  ?? "—" },
    { label: "EPS",          value: data.eps          ?? "—" },
    { label: "Analyst Tgt",  value: data.analyst_target ? `$${Number(data.analyst_target).toFixed(2)}` : "—" },
  ].filter((r) => r.value !== "—");

  return (
    <div className="market-card">
      <div className="market-card-header">
        <span className="market-ticker">{data.ticker}</span>
        <span className="market-price">{rows.find(r => r.label === "Price")?.value ?? "—"}</span>
      </div>
      <dl className="market-dl">
        {rows
          .filter((r) => r.label !== "Price")
          .map((r) => (
            <div key={r.label} className="market-row">
              <dt className="market-label">{r.label}</dt>
              <dd className="market-value">{r.value}</dd>
            </div>
          ))}
      </dl>
    </div>
  );
}

function SourceCard({ source, index }) {
  const [open, setOpen] = useState(false);
  const scorePercent    = source.score ? Math.round(source.score * 100) : null;

  return (
    <div className={`source-card ${open ? "open" : ""}`}>
      <button className="source-header" onClick={() => setOpen(!open)}>
        <div className="source-meta">
          <span className="source-num">Source {source.index ?? index + 1}</span>
          <span className="source-ticker-badge">{source.ticker}</span>
          {source.chunk_index != null && (
            <span className="source-chunk">chunk #{source.chunk_index}</span>
          )}
        </div>
        <div className="source-right">
          {scorePercent != null && (
            <span className="source-score">{scorePercent}% match</span>
          )}
          <span className={`chevron ${open ? "up" : "down"}`}>›</span>
        </div>
      </button>
      {open && (
        <div className="source-body">
          <p className="source-snippet">{source.snippet}</p>
        </div>
      )}
    </div>
  );
}

// ─── Main component ──────────────────────────────────────────────────────────

export default function AnswerPanel({ result, loading, question }) {
  const [sourcesOpen, setSourcesOpen] = useState(false);

  if (loading) {
    return (
      <div className="answer-panel">
        <div className="answer-loading-label">
          <span className="pulse-dot" />
          Querying filings…
        </div>
        <SkeletonLoader />
      </div>
    );
  }

  if (!result) return null;

  const { answer, sources = [], market_data = [] } = result;

  return (
    <div className="answer-panel">
      {/* Question echo */}
      <p className="answer-question">"{question}"</p>

      {/* Answer body */}
      <div className="answer-body">
        {parseAnswer(answer)}
      </div>

      {/* Market data */}
      <MarketDataBlock items={market_data} />

      {/* Sources */}
      {sources.length > 0 && (
        <div className="sources-section">
          <button
            className="sources-toggle"
            onClick={() => setSourcesOpen(!sourcesOpen)}
          >
            <span className="block-icon">⊞</span>
            {sources.length} Filing Source{sources.length !== 1 ? "s" : ""}
            <span className={`chevron ${sourcesOpen ? "up" : "down"}`}>›</span>
          </button>
          {sourcesOpen && (
            <div className="sources-list">
              {sources.map((s, i) => (
                <SourceCard key={i} source={s} index={i} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
