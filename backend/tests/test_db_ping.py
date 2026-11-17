from contextlib import contextmanager

from fastapi.testclient import TestClient

import app.main as main

client = TestClient(main.app)


class _FakeCursor:
    def execute(self, sql):
        self.sql = sql

    def fetchone(self):
        return (2000,)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConn:
    def cursor(self):
        return _FakeCursor()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_db_ping_ok(monkeypatch):
    monkeypatch.setattr(main, "get_connection", lambda: _FakeConn())
    response = client.get("/db-ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "chunks": 2000}


def test_db_ping_db_down(monkeypatch):
    def boom():
        raise RuntimeError("connection refused")

    monkeypatch.setattr(main, "get_connection", boom)
    response = client.get("/db-ping")
    assert response.status_code == 503
    assert "database unreachable" in response.json()["detail"]
