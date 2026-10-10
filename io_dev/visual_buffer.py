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
        for entry in self.buffer:
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
                    screenshot = pyautogui.screenshot()
                    screenshot = screenshot.resize((800, 450))
                    screenshot.save(self.temp_image_path, "JPEG", quality=70)

                    if os.path.exists(self.temp_image_path):
                        with open(self.temp_image_path, "rb") as image_file:
                            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

                        summary = await self._analyze_image_local(base64_image)
                        self.buffer.append({
                            "timestamp": time.time(),
                            "summary": f"Visual observation: {summary}"
                        })
                        try:
                            os.remove(self.temp_image_path)
                        except OSError:
                            pass
                else:
                    win_info = context_tools.get_screen_context().replace(", sir.", "")
                    clipboard = context_tools.get_clipboard_text()
                    summary = f"User is looking at {win_info}."
                    if "empty" not in clipboard.lower() and len(clipboard) < 150:
                        # Keep escaping/cleanup outside the f-string expression for Python compatibility.
                        cleaned_clipboard = clipboard.replace('Clipboard Content:\n"""', "").replace('"""', "").strip()
                        summary += f" Clipboard text contains: '{cleaned_clipboard}'."

                    self.buffer.append({
                        "timestamp": time.time(),
                        "summary": summary
                    })
            except Exception:
                # Background observation should not crash the main agent loop.
                pass

            await asyncio.sleep(config.VISUAL_BUFFER_INTERVAL)

    def stop(self):
        """Stops the visual buffer loop."""
        self.is_running = False

    async def _analyze_image_local(self, base64_image: str) -> str:
        """Calls local Ollama vision model to summarize screen image."""
        payload = {
            "model": config.VISION_MODEL,
            "messages": [{
                "role": "user",
                "content": "Describe what software application or website the user is looking at and any errors visible in 1 short sentence.",
                "images": [base64_image]
            }],
            "stream": False
        }
        try:
            response = await asyncio.to_thread(
                requests.post,
                f"{config.OLLAMA_URL}/api/chat",
                json=payload,
                timeout=12
            )
            if response.status_code == 200:
                return response.json().get("message", {}).get("content", "").strip()
            return f"Vision model status: {response.status_code}"
        except Exception as exc:
            return f"Vision processing offline: {exc}"

if __name__ == "__main__":
    buffer = JarvisVisualBuffer()

    async def run_test():
        await asyncio.sleep(0.5)
        await buffer.run_loop()
        print(buffer.get_context_summary())

    try:
        asyncio.run(asyncio.wait_for(run_test(), timeout=5))
    except asyncio.TimeoutError:
        print("Visual buffer test finished.")
