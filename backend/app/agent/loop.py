"""
Agent loop for FinSight.

Pattern: two-turn Gemini interaction.
  Turn 1 (routing)   — Gemini sees the question + tool schemas, decides which tools to call.
  [execution]        — We run the selected tools (retriever, yfinance).
  Turn 2 (synthesis) — Gemini sees all tool results and writes the final cited answer.

Fallback: if Turn 1 produces no function calls, we run a direct RAG retrieval.
"""

import json
from google import genai
from google.genai import types

from app.core.config import settings
from app.retrieval.retriever import retrieve
from app.tools.market import get_market_data
from app.agent.ticker import extract_tickers

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.llm_api_key)
    return _client

# Tool Schema

_TOOLS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="search_filings",
            description=(
                "Search AAPL, MSFT, and NVDA SEC 10-K filings for relevant passages. "
                "Use for any question about risks, strategy, revenue breakdown, products, "
                "competition, R&D, management discussion, guidance, or other disclosures."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "question": types.Schema(
                        type=types.Type.STRING,
                        description="The question or search query to run against the filings.",
                    ),
                    "ticker": types.Schema(
                        type=types.Type.STRING,
                        description=(
                            "Restrict search to one ticker: AAPL, MSFT, or NVDA. "
                            "Omit to search all three."
                        ),
                    ),
                    "top_k": types.Schema(
                        type=types.Type.INTEGER,
                        description="Number of chunks to retrieve. Default 5, max 10.",
                    ),
                },
                required=["question"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_market_data",
            description=(
                "Get live market data for a stock: price, market cap, P/E ratio, "
                "52-week high/low, revenue, EPS. Use when the question asks about "
                "current price, valuation, or recent market performance."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "ticker": types.Schema(
                        type=types.Type.STRING,
                        description="Ticker symbol, e.g. NVDA, AAPL, MSFT.",
                    ),
                },
                required=["ticker"],
            ),
        ),
    ]
)

# Prompts

_ROUTER_SYSTEM = """\
You are a financial research assistant routing a user question to the right data sources.

Available tools:
- search_filings: retrieves passages from AAPL, MSFT, NVDA 10-K SEC filings.
- get_market_data: returns live price, market cap, P/E, and other market stats.

Rules:
- Call search_filings for any question about company disclosures, risks, strategy, or financials from annual reports.
- Call get_market_data for any question about current price, market cap, or valuation.
- Call both if the question mixes filing disclosures with current market context.
- You may call search_filings multiple times with different tickers if the question spans companies.
- Do NOT write an answer yet. Call tools only.
"""

_SYNTHESIS_SYSTEM = """\
You are FinSight, a financial research assistant. Answer the question using ONLY the \
tool results below. Do not use prior knowledge.

Rules:
- Cite every factual claim from filings as [Source N] immediately after the claim.
- Cite market data facts as [Market Data].
- If multiple sources support a claim, cite all: [Source 1][Source 3].
- If the sources don't contain enough information, say so explicitly.
- Be concise and direct. No padding or filler sentences.
"""

# Agent entry point

def run(question: str, ticker_hint: str | None = None) -> dict:
    """
    Run the agent on a user question.

    Args:
        question:    Natural-language question from the user.
        ticker_hint: Optional ticker from the API request (overrides auto-detection).

    Returns:
        {
            "answer":      str,          # cited prose answer
            "sources":     list[dict],   # filing chunks used
            "market_data": list[dict],   # live market data fetched (may be empty)
        }
    """
    # Auto-detect tickers; hint takes priority
    tickers = extract_tickers(question)
    if ticker_hint:
        t = ticker_hint.upper()
        tickers = [t] + [x for x in tickers if x != t]

    ticker_note = f"[Tickers detected: {', '.join(tickers)}] " if tickers else ""
    routed_q = f"{ticker_note}{question}"

    # Turn 1: routing — Gemini picks tools
    r1 = _get_client().models.generate_content(
        model=settings.llm_model,
        contents=routed_q,
        config=types.GenerateContentConfig(
            system_instruction=_ROUTER_SYSTEM,
            tools=[_TOOLS],
        ),
    )


    # Execute tool calls
    rag_chunks: list[dict] = []
    market_results: list[dict] = []
    called_any = False

    parts = r1.candidates[0].content.parts if r1.candidates else []

    for part in parts:
        if not part.function_call:
            continue
        called_any = True
        fc = part.function_call
        args = dict(fc.args) if fc.args else {}

        if fc.name == "search_filings":
            # Use hinted/detected ticker unless the model explicitly chose one
            ticker_arg = args.get("ticker") or (tickers[0] if tickers else None)
            chunks = retrieve(
                question=args.get("question", question),
                top_k=min(int(args.get("top_k", 5)), 10),
                ticker=ticker_arg,
            )
            # Deduplicate by (ticker, chunk_index) in case called twice
            seen_ids = {(c["ticker"], c["chunk_index"]) for c in rag_chunks}
            for c in chunks:
                key = (c["ticker"], c["chunk_index"])
                if key not in seen_ids:
                    rag_chunks.append(c)
                    seen_ids.add(key)

        elif fc.name == "get_market_data":
            ticker_arg = args.get("ticker") or (tickers[0] if tickers else "")
            if ticker_arg:
                market_results.append(get_market_data(ticker_arg))

    # Fallback: no tool calls — do a direct RAG retrieval
    if not called_any:
        rag_chunks = retrieve(question, top_k=5, ticker=tickers[0] if tickers else None)

    if not rag_chunks and not market_results:
        return {
            "answer": "I couldn't find relevant information to answer that question.",
            "sources": [],
            "market_data": [],
        }


    # Build synthesis context
    context_parts: list[str] = []

    if rag_chunks:
        filing_block = "\n\n".join(
            f"[Source {i + 1} | {c['ticker']} chunk {c['chunk_index']} | score {c['score']}]\n{c['content']}"
            for i, c in enumerate(rag_chunks)
        )
        context_parts.append(f"=== Filing Sources ===\n{filing_block}")

    if market_results:
        market_block = "\n\n".join(
            f"[Market Data | {m['ticker']}]\n{json.dumps(m, indent=2)}"
            for m in market_results
        )
        context_parts.append(f"=== Live Market Data ===\n{market_block}")

    synthesis_prompt = "\n\n".join(context_parts) + f"\n\nQuestion: {question}"

    # Turn 2: synthesis — Gemini writes the cited answer
    r2 = _get_client().models.generate_content(
        model=settings.llm_model,
        contents=synthesis_prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYNTHESIS_SYSTEM,
        ),
    )

    return {
        "answer": r2.text,
        "sources": [
            {
                "index": i + 1,
                "ticker": c["ticker"],
                "chunk_index": c["chunk_index"],
                "score": c["score"],
                "snippet": c["content"][:400] + ("…" if len(c["content"]) > 400 else ""),
            }
            for i, c in enumerate(rag_chunks)
        ],
        "market_data": market_results,
    }
