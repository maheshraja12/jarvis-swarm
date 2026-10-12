"""Security tests for opt-in dynamic Python tool loading."""
import json

from tools.custom_manager import CustomToolManager


def _schema(name="safe_add"):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": "Adds two numbers.",
            "parameters": {
                "type": "object",
                "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                "required": ["a", "b"],
            },
        },
    }


def test_custom_python_tools_are_disabled_by_default(monkeypatch, tmp_path):
    monkeypatch.delenv("JARVIS_ENABLE_UNSAFE_CUSTOM_TOOLS", raising=False)
    manager = CustomToolManager(tools_dir=str(tmp_path))
    result = manager.register_new_tool("safe_add", "def safe_add(a, b): return a + b", _schema())

    assert "disabled by default" in result
    assert manager.custom_tools == {}
    assert not (tmp_path / "custom_safe_add.py").exists()


def test_custom_tool_name_cannot_escape_tools_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("JARVIS_ENABLE_UNSAFE_CUSTOM_TOOLS", "1")
    manager = CustomToolManager(tools_dir=str(tmp_path))
    result = manager.register_new_tool("../outside", "def x(): return 1", _schema("../outside"))

    assert "Invalid tool name" in result
    assert list(tmp_path.iterdir()) == []


def test_explicit_opt_in_loads_operator_reviewed_tool(monkeypatch, tmp_path):
    monkeypatch.setenv("JARVIS_ENABLE_UNSAFE_CUSTOM_TOOLS", "1")
    manager = CustomToolManager(tools_dir=str(tmp_path))
    code = "def safe_add(a: int, b: int) -> int:\n    return a + b\n"
    result = manager.register_new_tool("safe_add", code, _schema())

    assert "syntax-checked and loaded" in result
    assert manager.custom_tools["safe_add"](2, 3) == 5


def test_existing_custom_tools_are_not_imported_without_opt_in(monkeypatch, tmp_path):
    monkeypatch.delenv("JARVIS_ENABLE_UNSAFE_CUSTOM_TOOLS", raising=False)
    (tmp_path / "custom_persisted.py").write_text(
        "raise RuntimeError('should not be imported')\ndef persisted(): return True\n",
        encoding="utf-8",
    )
    (tmp_path / "tool_schemas.json").write_text(
        json.dumps({"persisted": _schema("persisted")}), encoding="utf-8"
    )

    manager = CustomToolManager(tools_dir=str(tmp_path))

    assert manager.custom_tools == {}
