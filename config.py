import os

# Central Configuration for JARVIS Swarm (v3.0)

# ========================================================================
# 1. CLOUD BRAIN SETTINGS (Primary - connects to internet, blazing fast)
# ========================================================================
# Get your FREE API key from: https://console.groq.com/keys
# Sign up takes 30 seconds. Groq runs Llama-3 at 500+ tokens/sec for free.
GROQ_API_KEY = ""  # <-- PASTE YOUR FREE GROQ API KEY HERE
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"  # Powerful 70B model, runs free on Groq

# ========================================================================
# 2. LOCAL BRAIN FALLBACK (Ollama - optional, used if cloud is unavailable)
# ========================================================================
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "qwen2.5:1.5b"
ENGINEER_MODEL = "qwen2.5:1.5b"
VISION_MODEL = "llava:7b"

# ========================================================================
# 3. BRAIN MODE: "cloud" | "local" | "auto"
# ========================================================================
# "cloud"  = Always use Groq cloud API (requires internet + API key)
# "local"  = Always use Ollama local LLM (requires Ollama running)
# "auto"   = Try cloud first, fall back to local Ollama, then pattern-matching
BRAIN_MODE = "auto"

# 4. Text-to-Speech (TTS) Settings
DEFAULT_TTS_ENGINE = "edge-tts"
EDGE_TTS_VOICE = "en-US-ChristopherNeural"
PYTTSX3_RATE = 185

# 5. Speech-to-Text (STT) Settings
STT_ENERGY_THRESHOLD = 300
STT_RECORD_TIMEOUT = 10

# 6. Long-Term Memory Settings
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_memory.db")

# 7. Assistant Trigger Settings
TRIGGER_MODE = "hybrid"
WAKE_WORDS = ["jarvis", "friday", "hey jarvis"]
HOTKEY_TRIGGER = "ctrl+shift+j"

# 8. Screen Context & App Settings
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# 9. Swarm & Custom Tools Settings
ENABLE_SWARM = True
CUSTOM_TOOLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_tools")
os.makedirs(CUSTOM_TOOLS_DIR, exist_ok=True)

# 10. Visual Buffer Settings
ENABLE_VISION = False
VISUAL_BUFFER_INTERVAL = 8
VISUAL_BUFFER_LIMIT = 5

# 11. Web HUD Dashboard Settings
# Set to True to enable the dashboard HUD at port 8000, or False for an invisible background voice mode.
ENABLE_WEB_SERVER = True
