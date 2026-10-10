"""Security regression tests for the JARVIS web API."""
from fastapi.testclient import TestClient

from brain.web_server import app


def test_remote_sensitive_route_fails_closed_without_token(monkeypatch):
    monkeypatch.delenv("JARVIS_API_TOKEN", raising=False)
    client = TestClient(app, client=("203.0.113.7", 12345))
    response = client.post("/api/command", json={"command": "hello"})
    assert response.status_code == 503
    assert "JARVIS_API_TOKEN" in response.json()["detail"]


def test_sensitive_route_requires_matching_token_when_configured(monkeypatch):
    monkeypatch.setenv("JARVIS_API_TOKEN", "test-secret-token")
    client = TestClient(app, client=("203.0.113.7", 12345))

    missing = client.post("/api/command", json={"command": "hello"})
    wrong = client.post(
        "/api/command",
        json={"command": "hello"},
        headers={"X-JARVIS-Token": "wrong-token"},
    )
    authorized = client.post(
        "/api/command",
        json={"command": "hello"},
        headers={"X-JARVIS-Token": "test-secret-token"},
    )

    assert missing.status_code == 401
    assert wrong.status_code == 401
    # Authentication succeeded; the local agent is intentionally not started in this test.
    assert authorized.status_code == 503
    assert "initializing" in authorized.json()["detail"].lower()


def test_loopback_development_mode_remains_available_without_token(monkeypatch):
    monkeypatch.delenv("JARVIS_API_TOKEN", raising=False)
    client = TestClient(app, client=("127.0.0.1", 12345))
    response = client.post("/api/command", json={"command": "hello"})
    assert response.status_code == 503
    assert "initializing" in response.json()["detail"].lower()


def test_cors_does_not_allow_arbitrary_origin():
    client = TestClient(app)
    response = client.options(
        "/api/command",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in response.headers
