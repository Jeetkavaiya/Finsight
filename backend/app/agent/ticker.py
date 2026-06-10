import re

_NAME_MAP: dict[str, str] = {
    "nvidia": "NVDA",
    "nvda": "NVDA",
    "apple": "AAPL",
    "aapl": "AAPL",
    "microsoft": "MSFT",
    "msft": "MSFT",
    "alphabet": "GOOGL",
    "google": "GOOGL",
    "googl": "GOOGL",
    "meta": "META",
    "facebook": "META",
    "amazon": "AMZN",
    "amzn": "AMZN",
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "jpm": "JPM",
    "bank of america": "BAC",
    "bac": "BAC",
    "goldman sachs": "GS",
    "goldman": "GS",
    "gs": "GS",
    "morgan stanley": "MS",
    "johnson & johnson": "JNJ",
    "johnson and johnson": "JNJ",
    "jnj": "JNJ",
    "pfizer": "PFE",
    "pfe": "PFE",
    "unitedhealth": "UNH",
    "united health": "UNH",
    "unh": "UNH",
    "exxon": "XOM",
    "exxon mobil": "XOM",
    "xom": "XOM",
    "chevron": "CVX",
    "cvx": "CVX",
    "tesla": "TSLA",
    "tsla": "TSLA",
    "walmart": "WMT",
    "wmt": "WMT",
    "coca-cola": "KO",
    "coca cola": "KO",
    "coke": "KO",
    "ko": "KO",
    "disney": "DIS",
    "dis": "DIS",
    "netflix": "NFLX",
    "nflx": "NFLX",
}

_KNOWN_TICKERS: frozenset[str] = frozenset({
    "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN",
    "JPM", "BAC", "GS", "MS",
    "JNJ", "PFE", "UNH",
    "XOM", "CVX",
    "TSLA", "WMT", "KO", "DIS", "NFLX",
})

_TICKER_RE = re.compile(r"\b([A-Z]{2,5})\b")


def extract_tickers(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    text_lower = text.lower()

    for name, ticker in _NAME_MAP.items():
        if name in text_lower and ticker not in seen:
            found.append(ticker)
            seen.add(ticker)

    for match in _TICKER_RE.finditer(text):
        candidate = match.group(1)
        if candidate in _KNOWN_TICKERS and candidate not in seen:
            found.append(candidate)
            seen.add(candidate)

    return found