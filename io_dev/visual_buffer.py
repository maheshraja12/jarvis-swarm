import asyncio
import os
import sys
import base64
import collections
import time
import requests
from collections import deque
import pyautogui

# Add parent directory to path to allow importing config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from tools import context_tools

class JarvisVisualBuffer:
    """Manages background screen capture and maintains ambient screen context."""
    
    def __init__(self):
        self.buffer = deque(maxlen=config.VISUAL_BUFFER_LIMIT)
        self.is_running = False
        self.temp_image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_vision_capture.jpg")

    def get_context_summary(self) -> str:
        """Returns the current accumulated screen history context string."""
        if not self.buffer:
            return "No ambient screen context is currently recorded, sir."
            
        context_lines = []
        # Return context from oldest to newest
        for idx, entry in enumerate(self.buffer):
            time_diff = int(time.time() - entry["timestamp"])
            context_lines.append(f"[{time_diff}s ago] {entry['summary']}")
            
        return "Ambient Screen History (latest actions):\n" + "\n".join(context_lines)

    async def run_loop(self):
        """Starts the periodic background screenshot capture and analysis loop."""
        self.is_running = True
        print(f"[Visual Buffer] Ambient context loop started (Interval: {config.VISUAL_BUFFER_INTERVAL}s).")
        
        while self.is_running:
            try:
                if config.ENABLE_VISION:
                    # 1. Take a screenshot using pyautogui
                    screenshot = pyautogui.screenshot()
                    # Scale down the screenshot to keep it fast and reduce payload
                    screenshot = screenshot.resize((800, 450)) # 16:9 ratio
                    screenshot.save(self.temp_image_path, "JPEG", quality=70)
                    
                    if os.path.exists(self.temp_image_path):
                        # 2. Convert to base64
                        with open(self.temp_image_path, "rb") as image_file:
                            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
                        
                        # 3. Call local Ollama vision endpoint
                        summary = await self._analyze_image_local(base64_image)
                        
                        # 4. Append to buffer
                        self.buffer.append({
                            "timestamp": time.time(),
                            "summary": f"Visual observation: {summary}"
                        })
                        
                        # Clean up
                        try:
                            os.remove(self.temp_image_path)
                        except Exception:
                            pass
                else:
                    # Fallback to Text-Based Context tracking (zero VRAM overhead, works in sandboxes)
                    win_info = context_tools.get_screen_context().replace(", sir.", "")
                    clipboard = context_tools.get_clipboard_text()
                    
                    summary = f"User is looking at {win_info}."
                    if "empty" not in clipboard.lower() and len(clipboard) < 150:
                        # Append a snippet of the clipboard if relevant and short
                        summary += f" Clipboard text contains: '{clipboard.replace('Clipboard Content:\n\"\"\"', '').replace('\"\"\"', '').strip()}'."
                    
                    self.buffer.append({
                        "timestamp": time.time(),
                        "summary": summary
                    })
                    
            except Exception as e:
                # Silently catch background errors to avoid crashing the main loop
                pass
                
            await asyncio.sleep(config.VISUAL_BUFFER_INTERVAL)

    def stop(self):
        """Stops the visual buffer loop."""
        self.is_running = False

    async def _analyze_image_local(self, base64_image: str) -> str:
        """Calls local Ollama vision model to summarize screen image."""
        payload = {
            "model": config.VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": "Describe what software application or website the user is looking at and any errors visible in 1 short sentence.",
                    "images": [base64_image]
                }
            ],
            "stream": False
        }
        try:
            # Query Ollama with a timeout of 10s
            response = await asyncio.to_thread(
                requests.post,
                f"{config.OLLAMA_URL}/api/chat",
                json=payload,
                timeout=12
            )
            if response.status_code == 200:
                return response.json().get("message", {}).get("content", "").strip()
            return f"Vision model status: {response.status_code}"
        except Exception as e:
            return f"Vision processing offline: {e}"

# Simple self-test if run directly
if __name__ == "__main__":
    buffer = JarvisVisualBuffer()
    async def run_test():
        # Test text-based fallback
        await asyncio.sleep(0.5)
        # Manually run a single iteration
        await buffer.run_loop()
        print(buffer.get_context_summary())
        
    try:
        asyncio.run(asyncio.wait_for(run_test(), timeout=5))
    except asyncio.TimeoutError:
        print("Visual buffer test finished.")
