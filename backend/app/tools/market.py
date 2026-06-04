from datetime import datetime, timezone
import yfinance as yf


def get_market_data(ticker: str) -> dict:
    """
    Fetch live market data for a ticker via yfinance.

    Returns a flat dict suitable for JSON serialization and Gemini context injection.
    Always returns a dict — errors are surfaced as {"error": "..."} so the agent
    can handle them gracefully rather than crashing.
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        # yfinance returns a mostly-empty dict for invalid tickers
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if not info or price is None:
            return {"ticker": ticker.upper(), "error": "No market data found — ticker may be invalid or market closed."}

        def _fmt_large(n):
            """Turn 3_000_000_000 → '$3.00B' for readability in the LLM context."""
            if n is None:
                return None
            if n >= 1e12:
                return f"${n / 1e12:.2f}T"
            if n >= 1e9:
                return f"${n / 1e9:.2f}B"
            if n >= 1e6:
                return f"${n / 1e6:.2f}M"
            return f"${n:,.0f}"

        return {
            "ticker": ticker.upper(),
            "price": round(price, 2),
            "currency": info.get("currency", "USD"),
            "market_cap": _fmt_large(info.get("marketCap")),
            "pe_ratio_trailing": round(info.get("trailingPE"), 2) if info.get("trailingPE") else None,
            "pe_ratio_forward": round(info.get("forwardPE"), 2) if info.get("forwardPE") else None,
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "revenue_ttm": _fmt_large(info.get("totalRevenue")),
            "eps_ttm": info.get("trailingEps"),
            "analyst_target_price": info.get("targetMeanPrice"),
            "as_of_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }

    except Exception as exc:
        return {"ticker": ticker.upper(), "error": str(exc)}