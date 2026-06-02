"""
JARVIS Cloud Brain - Connects to Groq's free ultra-fast LLM API.
Supports full function/tool calling with Llama-3 70B at 500+ tokens/sec.
Falls back gracefully to local pattern-matching brain if offline.
"""

import asyncio
import json
import os
import sys
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from brain.prompt import SYSTEM_PROMPT, TOOLS
from brain.memory import JarvisMemory
from tools import system_tools, context_tools, file_tools, web_tools


class CloudBrain:
    """Connects to Groq's free cloud LLM API with full tool-calling support."""

    def __init__(self):
        self.memory = JarvisMemory()
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Map tool names to callable functions
        self.tool_mapping = {
            "run_application": system_tools.run_application,
            "get_system_stats": system_tools.get_system_stats,
            "adjust_system_volume": system_tools.adjust_system_volume,
            "take_screenshot": system_tools.take_screenshot,
            "get_screen_context": context_tools.get_screen_context,
            "get_clipboard_text": context_tools.get_clipboard_text,
            "search_files": file_tools.search_files,
            "web_search": web_tools.web_search,
            "get_weather_and_time": web_tools.get_weather_and_time,
            "remember_fact": self.memory.store,
            "recall_fact": self.memory.recall,
            "delete_memory_fact": self.memory.delete,
            "list_all_memories": self.memory.list_all,
        }

    def is_available(self) -> bool:
        """Checks if the Groq cloud brain has a valid API key configured."""
        return bool(config.GROQ_API_KEY and config.GROQ_API_KEY.strip())

    async def chat(self, user_input: str, visual_context: str = None) -> str:
        """Sends user message to Groq API, handles tool calls, returns final spoken response."""
        # Inject visual context into system prompt
        system_content = SYSTEM_PROMPT
        if visual_context:
            system_content += f"\n\nCURRENT AMBIENT CONTEXT:\n{visual_context}"
        self.history[0]["content"] = system_content

        self.history.append({"role": "user", "content": user_input})

        headers = {
            "Authorization": f"Bearer {config.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        # Convert our Ollama-style tool schemas to OpenAI-compatible format
        openai_tools = self._convert_tools_for_openai(TOOLS)

        loop_count = 0
        max_loops = 5

        while loop_count < max_loops:
            loop_count += 1

            payload = {
                "model": config.GROQ_MODEL,
                "messages": self.history,
                "tools": openai_tools if openai_tools else None,
                "tool_choice": "auto",
                "temperature": 0.7,
                "max_tokens": 1024,
            }
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}

            try:
                response = await asyncio.to_thread(
                    requests.post,
                    config.GROQ_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=15,
                )

                if response.status_code == 401:
                    return "My cloud brain API key is invalid, sir. Please check config.py and update your Groq API key."
                if response.status_code == 429:
                    return "I've hit the cloud rate limit temporarily, sir. Please try again in a moment."
                if response.status_code != 200:
                    return f"Cloud brain returned status {response.status_code}, sir. Falling back."

                res_json = response.json()
                choice = res_json.get("choices", [{}])[0]
                message = choice.get("message", {})

                # Store assistant message in history
                self.history.append(message)

                # Check for tool calls
                tool_calls = message.get("tool_calls", [])
                if not tool_calls:
                    return message.get("content", "I am at your service, sir.")

                # Execute tool calls
                for call in tool_calls:
                    func_info = call.get("function", {})
                    name = func_info.get("name", "")
                    args_str = func_info.get("arguments", "{}")
                    call_id = call.get("id", "")

                    # Parse arguments
                    try:
                        arguments = json.loads(args_str) if isinstance(args_str, str) else args_str
                    except json.JSONDecodeError:
                        arguments = {}

                    print(f"\n[JARVIS Cloud] Calling Tool: {name} with args: {arguments}")

                    if name in self.tool_mapping:
                        tool_func = self.tool_mapping[name]
                        try:
                            tool_response = await asyncio.to_thread(tool_func, **arguments)
                        except Exception as e:
                            tool_response = f"Error executing tool {name}: {e}"
                    else:
                        tool_response = f"Tool '{name}' is not registered."

                    print(f"[JARVIS Cloud] Tool Result: {tool_response}")

                    # Add tool response in OpenAI format
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": str(tool_response),
                    })

            except requests.exceptions.ConnectionError:
                self.history.pop()
                raise ConnectionError("Cloud brain is unreachable.")
            except requests.exceptions.Timeout:
                self.history.pop()
                raise ConnectionError("Cloud brain request timed out.")
            except Exception as e:
                return f"Cloud brain error: {e}"

        return "I have run too many operations for this command, sir."

    def _convert_tools_for_openai(self, tools: list) -> list:
        """Converts our tool schemas to OpenAI-compatible format for Groq."""
        converted = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                converted.append({
                    "type": "function",
                    "function": {
                        "name": func.get("name", ""),
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {"type": "object", "properties": {}}),
                    }
                })
        return converted

    def reset_history(self):
        """Clears conversation context."""
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]
