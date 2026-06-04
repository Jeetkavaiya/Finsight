import re

# Company name → ticker. Add more as you expand the corpus.
_NAME_MAP: dict[str, str] = {
    # NVDA
    "nvidia": "NVDA",
    "nvda": "NVDA",
    # AAPL
    "apple": "AAPL",
    "aapl": "AAPL",
    # MSFT
    "microsoft": "MSFT",
    "msft": "MSFT",
}

# Tickers we actually have data for
_KNOWN_TICKERS: frozenset[str] = frozenset({"AAPL", "MSFT", "NVDA"})

# Regex: 2–5 uppercase letters on a word boundary, not part of a longer word
_TICKER_RE = re.compile(r"\b([A-Z]{2,5})\b")


def extract_tickers(text: str) -> list[str]:
    """
    Extract recognized ticker symbols from natural-language text.

    Returns an ordered, deduplicated list of tickers found in `text`.
    Only returns tickers present in _KNOWN_TICKERS so random uppercase
    words (like "CEO" or "IPO") don't produce false positives.

    Examples:
        "What risks did Nvidia flag?" → ["NVDA"]
        "Compare Apple and MSFT margins" → ["AAPL", "MSFT"]
        "How is the market doing?" → []
    """
    found: list[str] = []
    seen: set[str] = set()
    text_lower = text.lower()

    # Name-based matches first (preserves natural mention order)
    for name, ticker in _NAME_MAP.items():
        if name in text_lower and ticker not in seen:
            found.append(ticker)
            seen.add(ticker)

    # Explicit ticker symbols (e.g. user typed "NVDA")
    for match in _TICKER_RE.finditer(text):
        candidate = match.group(1)
        if candidate in _KNOWN_TICKERS and candidate not in seen:
            found.append(candidate)
            seen.add(candidate)

    return found