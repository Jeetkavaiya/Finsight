import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

MOCK_ANSWER = "NVDA flagged risks related to supply chain and export controls."
MOCK_SOURCES = [
    {"index": 1, "ticker": "NVDA", "chunk_index": 3, "score": 0.91, "text": "..."}
]
MOCK_MARKET = [{"ticker": "NVDA", "price": 120.0, "market_cap": "2.95T"}]


def _mock_run(question, tickers=None):
    return {
        "answer": MOCK_ANSWER,
        "sources": MOCK_SOURCES,
        "market_data": MOCK_MARKET,
    }


@pytest.fixture(autouse=True)
def mock_agent(monkeypatch):
    monkeypatch.setattr("app.routers.query.run_query", _mock_run)


class TestQueryEndpoint:
    def test_filing_only(self):
        r = client.post(
            "/query",
            json={"question": "What risks did NVDA flag in their latest 10-K?", "ticker": "NVDA"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert "sources" in data
        assert isinstance(data["sources"], list)

    def test_missing_question_returns_422(self):
        r = client.post("/query", json={})
        assert r.status_code == 422

    def test_market_data_present(self):
        r = client.post(
            "/query",
            json={"question": "What is NVDA's current stock price?"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "market_data" in data

    def test_multi_ticker(self):
        r = client.post(
            "/query",
            json={"question": "How do Apple and Microsoft describe their competitive advantages?"},
        )
        assert r.status_code == 200
        assert len(r.json()["answer"]) > 0
