import asyncio
import os
import sys
import unittest
import shutil

from brain.memory import JarvisMemory
from brain.agent import JarvisAgent
from io_dev.audio_output import JarvisSpeaker
from io_dev.visual_buffer import JarvisVisualBuffer
from tools.custom_manager import CustomToolManager
from tools import system_tools, context_tools, file_tools, web_tools

class TestJarvisComponents(unittest.TestCase):
    
    def setUp(self):
        # Set up a test database for memory checks
        self.test_db = "test_memory_suite.db"
        self.memory = JarvisMemory(db_path=self.test_db)
        
        # Set up a test directory for dynamic tools
        self.test_tools_dir = "test_custom_tools_suite"
        self.tool_manager = CustomToolManager(tools_dir=self.test_tools_dir)
        
    def tearDown(self):
        # Clean up database file
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except Exception:
                pass
                
        # Clean up dynamic tools directory
        if os.path.exists(self.test_tools_dir):
            try:
                shutil.rmtree(self.test_tools_dir)
            except Exception:
                pass

    def test_memory_crud(self):
        """Tests storing, recalling, listing and deleting facts in long-term memory."""
        # 1. Store
        store_res = self.memory.store("owner favorite color", "crimson red")
        self.assertIn("Successfully stored", store_res)
        
        # 2. Recall
        recall_res = self.memory.recall("owner favorite")
        self.assertIn("crimson red", recall_res)
        
        # 3. List
        list_res = self.memory.list_all()
        self.assertIn("owner favorite color", list_res)
        self.assertIn("crimson red", list_res)
        
        # 4. Delete
        delete_res = self.memory.delete("owner favorite color")
        self.assertIn("Successfully deleted", delete_res)
        
        # Verify gone
        empty_res = self.memory.list_all()
        self.assertIn("My memory is currently empty", empty_res)

    def test_system_stats(self):
        """Tests that retrieving CPU, RAM and battery stats returns formatted system statistics."""
        stats = system_tools.get_system_stats()
        self.assertIn("CPU utilization", stats)
        self.assertIn("Memory usage", stats)

    def test_context_reading(self):
        """Tests screen context and active window title reading."""
        context = context_tools.get_screen_context()
        self.assertTrue(len(context) > 0)
        self.assertIn("Active window", context)

    def test_clipboard_retrieval(self):
        """Tests clipboard reading (even if empty)."""
        clipboard = context_tools.get_clipboard_text()
        self.assertTrue(len(clipboard) > 0)

    def test_speech_sanitization(self):
        """Tests that markdown and formatting symbols are removed from text to speak."""
        speaker = JarvisSpeaker()
        dirty = "**Warning, sir!** Please check this link: [Google](https://www.google.com). `Code` block here."
        clean = speaker._clean_for_speech(dirty)
        
        self.assertNotIn("**", clean)
        self.assertNotIn("`", clean)
        self.assertNotIn("https://", clean)
        self.assertIn("Warning, sir!", clean)
        self.assertIn("Google", clean)

    def test_visual_buffer_context(self):
        """Tests that Visual Buffer context captures and formats screen context history correctly."""
        visual_buffer = JarvisVisualBuffer()
        
        # Verify empty state
        self.assertIn("No ambient screen context", visual_buffer.get_context_summary())
        
        # Manually inject entries into buffer
        import time
        visual_buffer.buffer.append({
            "timestamp": time.time() - 10,
            "summary": "Visual observation: User is looking at VS Code IDE."
        })
        visual_buffer.buffer.append({
            "timestamp": time.time() - 2,
            "summary": "Visual observation: Compiler output shows error code 404."
        })
        
        summary = visual_buffer.get_context_summary()
        self.assertIn("Ambient Screen History", summary)
        self.assertIn("looking at VS Code IDE", summary)
        self.assertIn("shows error code 404", summary)

    def test_dynamic_tool_hotloading(self):
        """Tests compiling, saving, sandboxing and hot-loading a dynamically generated tool."""
        tool_code = """
def multiply_numbers(a: int, b: int) -> str:
    \"\"\"Multiplies two numbers together.\"\"\"
    return f"Product is {a * b}, sir."
"""
        tool_schema = {
            "type": "function",
            "function": {
                "name": "multiply_numbers",
                "description": "Multiplies two numbers.",
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
        
        # Register tool
        reg_result = self.tool_manager.register_new_tool("multiply_numbers", tool_code, tool_schema)
        self.assertIn("verified, sandboxed, and dynamically added", reg_result)
        
        # Test hotloaded tool call
        self.assertIn("multiply_numbers", self.tool_manager.custom_tools)
        func = self.tool_manager.custom_tools["multiply_numbers"]
        res = func(a=6, b=7)
        self.assertEqual(res, "Product is 42, sir.")

    def test_agent_graceful_fallback(self):
        """Tests that agent gracefully falls back to local brain when Ollama/Cloud are offline."""
        agent = JarvisAgent()
        import config
        old_url = config.OLLAMA_URL
        old_key = config.GROQ_API_KEY
        config.OLLAMA_URL = "http://localhost:9999"  # invalid port
        config.GROQ_API_KEY = ""  # no cloud key
        
        async def run_chat():
            return await agent.chat("hello")
            
        res = asyncio.run(run_chat())
        config.OLLAMA_URL = old_url
        config.GROQ_API_KEY = old_key
        
        # Agent should return a valid response from the local pattern brain, not crash
        self.assertTrue(len(res) > 0)
        self.assertIn("sir", res.lower())

if __name__ == "__main__":
    unittest.main()
