import requests
import json

BASE = "http://localhost:8000"

tests = [
    {
        "label": "Filing-only (NVDA risks)",
        "payload": {"question": "What risks did NVDA flag in their latest 10-K?", "ticker": "NVDA"},
    },
    {
        "label": "Mixed: filing + live market (NVDA valuation)",
        "payload": {"question": "What is NVDA's current stock price and what did they say about revenue growth in their 10-K?"},
    },
    {
        "label": "Multi-ticker (Apple vs Microsoft competition)",
        "payload": {"question": "How do Apple and Microsoft describe their competitive advantages?"},
    },
]

for t in tests:
    print(f"\n{'='*60}")
    print(f"TEST: {t['label']}")
    print(f"{'='*60}")

    r = requests.post(f"{BASE}/query", json=t["payload"])
    if r.status_code != 200:
        print(f"ERROR {r.status_code}: {r.text}")
        continue

    data = r.json()
    print(data["answer"])
    print("\n--- Sources ---")
    for s in data["sources"]:
        print(f"  [{s['index']}] {s['ticker']} chunk {s['chunk_index']} | score {s['score']}")

    if data["market_data"]:
        print("\n--- Market Data ---")
        for m in data["market_data"]:
            print(json.dumps(m, indent=2))