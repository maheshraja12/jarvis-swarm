import asyncio
import os
import sys
import re
import json
import requests

# Add parent directory to path to allow importing config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from brain.prompt import ENGINEER_PROMPT, CRITIC_PROMPT
from tools.custom_manager import CustomToolManager

class JarvisSwarm:
    """Manages the Multi-Agent Swarm (Engineer & Critic) for dynamic tool creation."""
    
    def __init__(self, custom_manager: CustomToolManager = None):
        self.custom_manager = custom_manager or CustomToolManager()

    async def create_tool(self, tool_name: str, specification: str) -> str:
        """Runs the Engineer-Critic loop to write, test, and register a new tool."""
        tool_name = re.sub(r'[^a-zA-Z0-9_]', '', tool_name.strip().replace(" ", "_")).lower()
        if not tool_name:
            return "Invalid tool name provided, sir."

        print(f"\n[Swarm] Command received: Create tool '{tool_name}' -> '{specification}'")
        
        code = ""
        feedback = ""
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            print(f"[Swarm] Swarm Engineer starting attempt {attempt}...")
            
            # 1. Ask Engineer to write code
            engineer_input = f"Create a tool named '{tool_name}' that implements the following specification:\n{specification}"
            if feedback:
                engineer_input += f"\n\nYour previous code failed code review with the following feedback:\n{feedback}\nPlease fix the issue and rewrite the function."

            code = await self._call_agent(config.ENGINEER_MODEL, ENGINEER_PROMPT, engineer_input)
            code = self._clean_code_blocks(code)
            
            if not code or "def " not in code:
                feedback = "Failed to output a valid Python function definition. Make sure your output contains a standard Python function starting with 'def'."
                print(f"[Swarm Warning] Engineer attempt {attempt} failed: {feedback}")
                continue

            print(f"[Swarm] Swarm Critic reviewing code for attempt {attempt}...")
            
            # 2. Ask Critic to verify code
            critic_input = f"Goal: {specification}\n\nGenerated Python Code:\n```python\n{code}\n```"
            critic_res = await self._call_agent(config.MODEL_NAME, CRITIC_PROMPT, critic_input)
            critic_res = critic_res.strip()
            
            print(f"[Swarm] Critic response: {critic_res}")
            
            if critic_res.upper() == "PASSED":
                print("[Swarm] Critic PASSED. Generating JSON schema...")
                
                # 3. Ask Ollama to write the JSON schema for this tool
                schema = await self._generate_schema(tool_name, specification, code)
                if not schema:
                    return f"Critic passed the code, but I failed to generate a valid schema representation, sir."

                # 4. Save and hot-load the tool
                register_res = self.custom_manager.register_new_tool(tool_name, code, schema)
                return register_res
            elif critic_res.upper().startswith("FAILED"):
                feedback = critic_res[7:].strip()
                print(f"[Swarm] Critic FAILED. Feedback: {feedback}")
            else:
                feedback = f"Critic did not return a clear PASSED or FAILED output. Critic output: {critic_res}"
                print(f"[Swarm Warning] Swarm Critic returned unexpected result: {feedback}")

        return f"Forgive me, sir, but after {max_attempts} attempts, my Swarm failed to create a stable tool. Critic feedback: {feedback}"

    async def _call_agent(self, model: str, system_prompt: str, user_prompt: str) -> str:
        """Invokes a local Ollama model context-free for swarm reasoning tasks."""
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }
        try:
            res = await asyncio.to_thread(
                requests.post,
                f"{config.OLLAMA_URL}/api/chat",
                json=payload,
                timeout=30
            )
            if res.status_code == 200:
                return res.json().get("message", {}).get("content", "")
            return f"Ollama HTTP error status: {res.status_code}"
        except Exception as e:
            return f"Agent connection error: {e}"

    def _clean_code_blocks(self, text: str) -> str:
        """Extracts the python block from markdown fenced code blocks if present."""
        if "```python" in text:
            match = re.search(r'```python\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                return match.group(1).strip()
        elif "```" in text:
            match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                return match.group(1).strip()
        return text.strip()

    async def _generate_schema(self, tool_name: str, specification: str, code: str) -> dict:
        """Asks Ollama to write the JSON schema corresponding to the tool signature."""
        prompt = (
            f"Generate a valid Ollama function tool declaration schema in JSON format "
            f"for a function named '{tool_name}' based on the following code:\n\n```python\n{code}\n```\n\n"
            f"The goal is: {specification}\n\n"
            f"Return ONLY the raw JSON block without markdown ```json and without explanations. "
            f"Match this schema pattern structure EXACTLY:\n"
            f'{{"type": "function", "function": {{"name": "{tool_name}", "description": "tool description", "parameters": {{"type": "object", "properties": {{}}, "required": []}}}}}}'
        )
        
        schema_text = await self._call_agent(config.MODEL_NAME, "You are a JSON schema writer. Return only JSON data. Output no conversational text.", prompt)
        
        # Clean markdown wrappers if any
        schema_text = self._clean_code_blocks(schema_text)
        
        try:
            schema = json.loads(schema_text)
            # Basic validation
            if "type" in schema and "function" in schema:
                # Force function name matching
                schema["function"]["name"] = tool_name
                return schema
        except Exception as e:
            print(f"[Swarm Warning] Failed to parse generated schema JSON: {e}. Raw: {schema_text}")
            
        # Standard fallback schema if model output failed to parse
        fallback_schema = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": specification[:100],
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
        return fallback_schema

# Simple self-test if run directly
if __name__ == "__main__":
    import shutil
    mgr = CustomToolManager("test_swarm_dir")
    swarm = JarvisSwarm(mgr)
    
    # Mock Ollama call test (will run against config URL)
    async def run_test():
        res = await swarm.create_tool("get_test_time", "return a string containing 'The system time is 12:00'")
        print(res)
        
    try:
        asyncio.run(run_test())
    except Exception as e:
        print(f"Direct test exception (expected if Ollama offline): {e}")
    finally:
        if os.path.exists("test_swarm_dir"):
            shutil.rmtree("test_swarm_dir")
