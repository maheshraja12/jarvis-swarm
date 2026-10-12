"""Regression tests for environment-driven JARVIS configuration."""
import importlib
import config


def test_cloud_api_key_is_read_from_environment(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key-not-a-real-secret")
    reloaded = importlib.reload(config)
    assert reloaded.GROQ_API_KEY == "test-key-not-a-real-secret"


def test_brain_mode_is_normalized(monkeypatch):
    monkeypatch.setenv("JARVIS_BRAIN_MODE", "LOCAL")
    reloaded = importlib.reload(config)
    assert reloaded.BRAIN_MODE == "local"


def test_invalid_brain_mode_fails_fast(monkeypatch):
    monkeypatch.setenv("JARVIS_BRAIN_MODE", "invalid")
    try:
        importlib.reload(config)
    except ValueError as exc:
        assert "JARVIS_BRAIN_MODE" in str(exc)
    else:
        raise AssertionError("Invalid brain mode must be rejected")
    finally:
        monkeypatch.setenv("JARVIS_BRAIN_MODE", "auto")
        importlib.reload(config)


def test_numeric_settings_are_configurable(monkeypatch):
    monkeypatch.setenv("JARVIS_TTS_RATE", "200")
    monkeypatch.setenv("JARVIS_VISUAL_BUFFER_INTERVAL", "0")
    reloaded = importlib.reload(config)
    assert reloaded.PYTTSX3_RATE == 200
    assert reloaded.VISUAL_BUFFER_INTERVAL == 1



def test_invalid_trigger_mode_fails_fast(monkeypatch):
    monkeypatch.setenv("JARVIS_TRIGGER_MODE", "unsupported")
    try:
        importlib.reload(config)
    except ValueError as exc:
        assert "JARVIS_TRIGGER_MODE" in str(exc)
    else:
        raise AssertionError("Invalid trigger mode must be rejected")
    finally:
        monkeypatch.setenv("JARVIS_TRIGGER_MODE", "hybrid")
        importlib.reload(config)
