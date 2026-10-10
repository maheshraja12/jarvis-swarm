import os

# Central Configuration for JARVIS Swarm (v3.0)

# Cloud credentials must be supplied through environment variables. Never commit
# API keys to the repository or embed them in static frontend code.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_API_URL = os.getenv(
    "GROQ_API_URL",
    "https://api.groq.com/openai/v1/chat/completions",
).strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

# Local brain fallback (Ollama)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
MODEL_NAME = os.getenv("JARVIS_MODEL_NAME", "qwen2.5:1.5b")
ENGINEER_MODEL = os.getenv("JARVIS_ENGINEER_MODEL", "qwen2.5:1.5b")
VISION_MODEL = os.getenv("JARVIS_VISION_MODEL", "llava:7b")

# Brain mode: "cloud" | "local" | "auto"
BRAIN_MODE = os.getenv("JARVIS_BRAIN_MODE", "auto").strip().lower()
if BRAIN_MODE not in {"cloud", "local", "auto"}:
    raise ValueError("JARVIS_BRAIN_MODE must be one of: cloud, local, auto")

# Text-to-speech
DEFAULT_TTS_ENGINE = os.getenv("JARVIS_TTS_ENGINE", "edge-tts")
EDGE_TTS_VOICE = os.getenv("JARVIS_TTS_VOICE", "en-US-ChristopherNeural")
PYTTSX3_RATE = int(os.getenv("JARVIS_TTS_RATE", "185"))

# Speech-to-text
STT_ENERGY_THRESHOLD = int(os.getenv("JARVIS_STT_ENERGY_THRESHOLD", "300"))
STT_RECORD_TIMEOUT = int(os.getenv("JARVIS_STT_RECORD_TIMEOUT", "10"))

# Long-term memory
DATABASE_PATH = os.getenv(
    "JARVIS_DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_memory.db"),
)

# Assistant trigger
TRIGGER_MODE = os.getenv("JARVIS_TRIGGER_MODE", "hybrid").strip().lower()
if TRIGGER_MODE not in {"voice", "keyboard", "hybrid"}:
    raise ValueError("JARVIS_TRIGGER_MODE must be one of: voice, keyboard, hybrid")
WAKE_WORDS = [
    word.strip().lower()
    for word in os.getenv("JARVIS_WAKE_WORDS", "jarvis,friday,hey jarvis").split(",")
    if word.strip()
]
HOTKEY_TRIGGER = os.getenv("JARVIS_HOTKEY_TRIGGER", "ctrl+shift+j")

# Screen context & app settings
SCREENSHOT_DIR = os.getenv(
    "JARVIS_SCREENSHOT_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots"),
)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Swarm & custom tools
ENABLE_SWARM = os.getenv("JARVIS_ENABLE_SWARM", "true").strip().lower() in {"1", "true", "yes", "on"}
CUSTOM_TOOLS_DIR = os.getenv(
    "JARVIS_CUSTOM_TOOLS_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_tools"),
)
os.makedirs(CUSTOM_TOOLS_DIR, exist_ok=True)

# Visual buffer
ENABLE_VISION = os.getenv("JARVIS_ENABLE_VISION", "false").strip().lower() in {"1", "true", "yes", "on"}
VISUAL_BUFFER_INTERVAL = max(1, int(os.getenv("JARVIS_VISUAL_BUFFER_INTERVAL", "8")))
VISUAL_BUFFER_LIMIT = max(1, int(os.getenv("JARVIS_VISUAL_BUFFER_LIMIT", "5")))

# Web HUD. Keep loopback-only by default; remote access requires deliberate review.
ENABLE_WEB_SERVER = os.getenv("JARVIS_ENABLE_WEB_SERVER", "true").strip().lower() in {"1", "true", "yes", "on"}
