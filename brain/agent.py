"""
JARVIS Unified Agent (v3.0)
Brain Priority: YOUR OWN Super Brain (primary) -> Cloud Groq (optional upgrade) -> Ollama (optional)
Your own brain runs first. Always. No dependencies.
"""

import json
import os
import sys
import asyncio
import re
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from brain.prompt import SYSTEM_PROMPT, TOOLS
from brain.memory import JarvisMemory
from brain.local_brain import SuperBrain
from brain.swarm import JarvisSwarm
from tools.custom_manager import CustomToolManager
from tools import system_tools, context_tools, file_tools, web_tools


class JarvisAgent:
    """Unified agent powered by your own self-contained Super Brain."""

    def __init__(self):
        self.memory = JarvisMemory()
        self.custom_manager = CustomToolManager()
        self.swarm = JarvisSwarm(self.custom_manager)
        self.running_tasks = {}
        self.task_counter = 0

        # YOUR OWN BRAIN - runs locally, no dependencies
        self.super_brain = SuperBrain()

        # Optional cloud brain (only used if user explicitly sets BRAIN_MODE = "cloud")
        self.cloud_brain = None
        self.active_brain = "super"  # Default: your own brain

        self._detect_brain()

    def _detect_brain(self):
        """Detects which brain mode to use based on config."""
        mode = config.BRAIN_MODE.lower()

        if mode == "cloud":
            try:
                from brain.cloud_brain import CloudBrain
                self.cloud_brain = CloudBrain()
                if self.cloud_brain.is_available():
                    self.active_brain = "cloud"
                    print("[Brain System] Mode: CLOUD (Groq API) - Online super intelligence active")
                else:
                    self.active_brain = "super"
                    print("[Brain System] Cloud mode requested but no API key. Using YOUR Super Brain.")
            except Exception:
                self.active_brain = "super"
                print("[Brain System] Cloud brain module error. Using YOUR Super Brain.")
        elif mode == "local":
            self.active_brain = "super"
            print("[Brain System] Mode: LOCAL - YOUR own Super Brain is active")
        else:  # auto
            # Try cloud first if API key exists
            try:
                from brain.cloud_brain import CloudBrain
                self.cloud_brain = CloudBrain()
                if self.cloud_brain.is_available():
                    self.active_brain = "cloud"
                    print("[Brain System] Mode: AUTO -> Cloud brain (Groq API) active")
                else:
                    self.active_brain = "super"
                    print("[Brain System] Mode: AUTO -> YOUR own Super Brain is active (no external dependencies)")
                    print("[Brain System] Your brain handles: apps, system, memory, math, search, screen, voice — all locally!")
            except Exception:
                self.active_brain = "super"
                print("[Brain System] YOUR own Super Brain is active (fully self-contained)")

    async def chat(self, user_input: str, visual_context: str = None) -> str:
        """Routes commands through the active brain with automatic fallback chain."""

        # --- CLOUD BRAIN (optional upgrade, only if user chose it) ---
        if self.active_brain == "cloud" and self.cloud_brain:
            try:
                response = await self.cloud_brain.chat(user_input, visual_context)
                return response
            except (ConnectionError, Exception) as e:
                print(f"[Brain System] Cloud brain error: {e}. Falling back to Super Brain.")
                # Fall through to Super Brain
                pass

        # --- YOUR OWN SUPER BRAIN (always available, zero dependencies) ---
        return self.super_brain.process(user_input, visual_context)

    def reset_history(self):
        """Clears conversation context across all brains."""
        self.super_brain.conversation.clear()
        if self.cloud_brain:
            self.cloud_brain.reset_history()
