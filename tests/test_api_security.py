"""Security regression tests for JARVIS API remote-access defaults."""
from fastapi.testclient import TestClient

from brain.web_server import app


def test_remote_api_fails_closed_without_token(monkeypatch):
    monkeypatch.delenv("JARVIS_API_TOKEN", raising=False)
    with TestClient(app, client=("203.0.113.10", 12345)) as client:
        response = client.get("/api/memory")
    assert response.status_code == 503
    assert "disabled" in response.json()["detail"].lower()


def test_remote_api_rejects_wrong_token(monkeypatch):
    monkeypatch.setenv("JARVIS_API_TOKEN", "test-secret-value")
    with TestClient(app, client=("203.0.113.10", 12345)) as client:
        response = client.get("/api/memory", headers={"X-JARVIS-Token": "wrong"})
    assert response.status_code == 401


def test_remote_api_accepts_configured_token_for_route(monkeypatch):
    monkeypatch.setenv("JARVIS_API_TOKEN", "test-secret-value")
    with TestClient(app, client=("203.0.113.10", 12345)) as client:
        response = client.get(
            "/api/memory",
            headers={"X-JARVIS-Token": "test-secret-value"},
        )
    # The request passes the access-control middleware. The handler may return
    # 200 or a generic 500 when the local database has not been initialized.
    assert response.status_code not in (401, 503)
