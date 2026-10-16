"""Runtime contract tests that do not require microphone or desktop hardware."""
from fastapi.testclient import TestClient

from brain.web_server import app, SwarmState


def test_health_and_root_hud_contract():
    with TestClient(app) as client:
        health = client.get("/health")
        root = client.get("/", follow_redirects=False)

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert root.status_code in (307, 308)
    assert root.headers["location"] == "/static/index.html"


def test_status_endpoint_returns_expected_telemetry_shape():
    with TestClient(app) as client:
        response = client.get("/api/status")

    assert response.status_code == 200
    body = response.json()
    assert {"cpu", "ram", "battery", "audio_status", "swarm_state", "custom_tools_count"} <= set(body)
    assert isinstance(body["cpu"], (int, float))
    assert isinstance(body["ram"], (int, float))
    assert {"charge", "plugged"} <= set(body["battery"])


def test_command_route_fails_closed_while_agent_is_unavailable(monkeypatch):
    monkeypatch.setattr(SwarmState, "agent_ref", None)
    with TestClient(app) as client:
        response = client.post("/api/command", json={"command": "hello"})

    assert response.status_code == 503
    assert "initializing" in response.json()["detail"].lower()


def test_command_payload_validation_happens_before_agent_access():
    with TestClient(app) as client:
        empty = client.post("/api/command", json={"command": "   "})
        too_long = client.post("/api/command", json={"command": "x" * 4001})

    assert empty.status_code == 422
    assert too_long.status_code == 422


def test_static_hud_asset_is_served():
    with TestClient(app) as client:
        response = client.get("/static/index.html")

    assert response.status_code == 200
    assert b"JARVIS" in response.content.upper()
