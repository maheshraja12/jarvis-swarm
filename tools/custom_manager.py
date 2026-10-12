import os
import sys
import importlib.util
import json
import re

# Add parent directory to path to allow importing config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

class CustomToolManager:
    """Manage optional custom Python tools; imported code runs with full process privileges."""

    @staticmethod
    def _unsafe_tools_enabled() -> bool:
        """Return whether the operator explicitly opted into arbitrary Python execution."""
        return os.getenv("JARVIS_ENABLE_UNSAFE_CUSTOM_TOOLS", "").strip().lower() in {"1", "true", "yes", "on"}
    
    def __init__(self, tools_dir=None):
        self.tools_dir = tools_dir or config.CUSTOM_TOOLS_DIR
        os.makedirs(self.tools_dir, exist_ok=True)
        self.schema_file = os.path.join(self.tools_dir, "tool_schemas.json")
        self.custom_tools = {}  # Mappings: {tool_name: callable_function}
        self.load_existing_tools()

    def load_existing_tools(self):
        """Load reviewed custom modules only when unsafe Python execution is explicitly enabled."""
        if not self._unsafe_tools_enabled():
            return
        if not os.path.exists(self.schema_file):
            return

        try:
            with open(self.schema_file, "r") as f:
                schemas = json.load(f)
        except Exception as e:
            print(f"[Tool Manager Warning] Could not read tool schemas file: {e}")
            return

        if not isinstance(schemas, dict):
            print("[Tool Manager Warning] Tool registry must be a JSON object.")
            return

        for tool_name, schema in schemas.items():
            if not isinstance(tool_name, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", tool_name):
                print("[Tool Manager Warning] Skipping invalid custom tool name.")
                continue
            filename = f"custom_{tool_name}.py"
            filepath = os.path.join(self.tools_dir, filename)
            
            if os.path.exists(filepath):
                success, func_or_err = self._load_module(tool_name, filepath)
                if success:
                    self.custom_tools[tool_name] = func_or_err
                    print(f"[Tool Manager] Successfully hot-loaded existing tool: '{tool_name}'")
                else:
                    print(f"[Tool Manager Warning] Failed to load tool '{tool_name}': {func_or_err}")

    def register_new_tool(self, tool_name: str, code: str, schema: dict) -> str:
        """Register trusted operator-reviewed code; this is not a security sandbox."""
        if not self._unsafe_tools_enabled():
            return ("Custom Python tool execution is disabled by default because imported code runs "
                    "with full JARVIS process privileges. Set JARVIS_ENABLE_UNSAFE_CUSTOM_TOOLS=1 "
                    "only for code you have reviewed and trust.")

        tool_name = (tool_name or "").strip().lower()
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", tool_name):
            return "Invalid tool name. Use 1-64 lowercase letters, numbers, and underscores; start with a letter."
        if not isinstance(code, str) or not isinstance(schema, dict):
            return "Invalid tool definition: code must be text and schema must be an object."
        filename = f"custom_{tool_name}.py"
        filepath = os.path.join(self.tools_dir, filename)

        # 1. Syntax check only. compile() does NOT sandbox or make Python code safe.
        try:
            compile(code, filepath, "exec")
        except SyntaxError as e:
            return f"Syntax verification failed: {e.msg} at line {e.lineno}"
        except Exception as e:
            return f"Code validation failed: {e}"

        # 2. Write the file
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            return f"Failed to write tool file: {e}"

        # 3. Hot-load into runtime
        success, func_or_err = self._load_module(tool_name, filepath)
        if not success:
            # Revert file write if loading failed
            try:
                os.remove(filepath)
            except Exception:
                pass
            return f"Sandbox execution failed: {func_or_err}"

        # 4. Save to memory registry
        self.custom_tools[tool_name] = func_or_err

        # 5. Save schema persistent registry
        schemas = {}
        if os.path.exists(self.schema_file):
            try:
                with open(self.schema_file, "r") as f:
                    schemas = json.load(f)
            except Exception:
                pass
                
        schemas[tool_name] = schema
        
        try:
            with open(self.schema_file, "w") as f:
                json.dump(schemas, f, indent=4)
        except Exception as e:
            print(f"[Tool Manager Warning] Could not save schema for '{tool_name}': {e}")

        return (f"Tool '{tool_name}' was syntax-checked and loaded. It executes with full JARVIS "
                "process privileges; only use operator-reviewed, trusted code.")

    def get_tool_schemas(self) -> list:
        """Returns the list of Ollama schemas for all custom tools."""
        if not os.path.exists(self.schema_file):
            return []
            
        try:
            with open(self.schema_file, "r") as f:
                schemas = json.load(f)
            return list(schemas.values())
        except Exception:
            return []

    def _load_module(self, name: str, filepath: str):
        """Import trusted Python code (not sandboxed) and return its primary function."""
        module_name = f"custom_tools.custom_{name}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                return False, "Could not load module specification."
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # The function must match the tool name
            if hasattr(module, name):
                func = getattr(module, name)
                if callable(func):
                    return True, func
                return False, f"Attribute '{name}' in module is not callable."
            else:
                # If no matching function, find any callable function in module
                callables = [getattr(module, a) for a in dir(module) if callable(getattr(module, a)) and not a.startswith("__")]
                if callables:
                    return True, callables[0]
                return False, f"Could not find any callable functions in '{filename}'."
        except Exception as e:
            return False, str(e)

# Simple self-test if run directly
if __name__ == "__main__":
    manager = CustomToolManager("test_custom_dir")
    
    test_code = """
def add_numbers(a: int, b: int) -> str:
    return f"Sum is {a + b}."
"""
    test_schema = {
        "type": "function",
        "function": {
            "name": "add_numbers",
            "description": "Adds two numbers together.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"}
                },
                "required": ["a", "b"]
            }
        }
    }
    
    # Test registration
    print(manager.register_new_tool("add_numbers", test_code, test_schema))
    
    # Test calling
    if "add_numbers" in manager.custom_tools:
        result = manager.custom_tools["add_numbers"](5, 7)
        print(f"Tool execution test: {result}")
        
    # Clean up
    if os.path.exists("test_custom_dir"):
        import shutil
        shutil.rmtree("test_custom_dir")
        print("Cleaned up test custom tools directory.")
