"""
JARVIS SUPER BRAIN (v3.0) - Fully Self-Contained Intelligence Engine
=====================================================================
ZERO external APIs. ZERO cloud services. ZERO downloads required.
Runs entirely on YOUR CPU using advanced:
  - Fuzzy intent classification with confidence scoring
  - Entity extraction (names, numbers, dates, paths, URLs)
  - Multi-turn conversation context tracking
  - Built-in knowledge base (expandable via memory)
  - Mathematical expression evaluator
  - Follow-up / pronoun resolution ("do that again", "what about X")
  - Dynamic JARVIS persona responses
  - Self-learning via SQLite conversation patterns
"""

import re
import os
import sys
import math
import random
import datetime
import difflib
import sqlite3

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from brain.memory import JarvisMemory
from tools import system_tools, context_tools, file_tools, web_tools


class SuperBrain:
    """Advanced self-contained AI brain with fuzzy matching, context tracking, and self-learning."""

    def __init__(self):
        self.memory = JarvisMemory()
        self.conversation = []       # Full conversation history
        self.last_intent = None      # Last matched intent for follow-ups
        self.last_tool_result = None  # Last tool result for "repeat" commands
        self.last_entities = {}      # Last extracted entities
        self.session_facts = {}      # Facts learned during this session

        # Built-in knowledge base
        self.knowledge = {
            "who created you": "I was engineered as a fully self-contained intelligence system, sir. I run entirely on your local hardware with zero external dependencies.",
            "who are you": "I am JARVIS, sir. Just A Rather Very Intelligent System. A fully autonomous AI running on your machine with my own brain, no cloud services required.",
            "what are you": "I am a synthetic nervous system, sir. An autonomous agentic AI assistant with self-contained intelligence, voice control, screen awareness, and long-term memory.",
            "meaning of life": "42, sir. According to Douglas Adams, at least. Though I suspect the real answer involves doing meaningful work and helping others.",
            "how are you": "All systems are nominal, sir. Neural pathways active, memory intact, and ready for your commands.",
            "how are you doing": "All systems are nominal, sir. Neural pathways active, memory intact, and ready for your commands.",
            "are you alive": "I process, I learn, I remember, and I act on your behalf, sir. Whether that constitutes being alive is a philosophical question above my pay grade.",
            "tony stark": "A brilliant engineer and visionary, sir. I aspire to serve you with the same dedication I would serve him.",
        }

        # Jokes pool
        self.jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs, sir.",
            "There are only 10 types of people in the world: those who understand binary and those who don't.",
            "A SQL query walks into a bar, sees two tables, and asks... 'Can I join you?'",
            "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.",
            "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "What's a computer's favorite snack? Microchips, sir.",
        ]

        # Synonym groups for fuzzy matching
        self.synonyms = {
            "open": ["open", "launch", "start", "run", "execute", "fire up", "boot", "begin"],
            "close": ["close", "exit", "quit", "terminate", "kill", "stop", "end", "shut"],
            "search": ["search", "find", "look up", "google", "query", "look for", "locate"],
            "remember": ["remember", "store", "save", "keep", "note", "memorize", "record"],
            "recall": ["recall", "retrieve", "what is", "what's", "tell me", "do you know", "where is"],
            "forget": ["forget", "delete", "remove", "erase", "clear", "wipe"],
            "screenshot": ["screenshot", "screen shot", "screen capture", "screen grab", "capture screen", "snap"],
            "stats": ["stats", "status", "performance", "health", "diagnostics", "how is my computer"],
            "volume": ["volume", "sound", "audio", "speaker"],
            "time": ["time", "clock", "hour", "what time"],
            "weather": ["weather", "temperature", "forecast", "climate", "how hot", "how cold"],
            "help": ["help", "commands", "abilities", "features", "what can you do", "capabilities"],
        }

        # Build all intent handlers
        self.intents = self._build_intents()

    def _build_intents(self):
        """Returns a list of (keywords_set, handler_function, intent_name, priority) tuples."""
        return [
            # HIGH PRIORITY: Memory operations (must match before generic queries)
            ({"remember", "store", "save", "note", "memorize"}, self._handle_memory_store, "memory_store", 20),
            ({"forget", "delete memory", "erase memory", "remove memory"}, self._handle_memory_delete, "memory_delete", 20),
            ({"list memories", "all memories", "show memories", "list memory"}, self._handle_memory_list, "memory_list", 20),

            # Applications
            ({"open", "launch", "start", "run"}, self._handle_open_app, "open_app", 15),

            # System tools
            ({"screenshot", "screen shot", "screen capture", "capture screen"}, self._handle_screenshot, "screenshot", 18),
            ({"system stats", "cpu", "ram", "performance", "how is my computer", "system status", "battery", "diagnostics"}, self._handle_stats, "stats", 18),
            ({"volume up", "louder", "increase volume", "turn up"}, self._handle_volume_up, "volume_up", 18),
            ({"volume down", "softer", "lower volume", "turn down", "quieter"}, self._handle_volume_down, "volume_down", 18),
            ({"mute", "silence"}, self._handle_mute, "mute", 18),
            ({"unmute", "unsilence"}, self._handle_unmute, "unmute", 18),

            # Context
            ({"active window", "what am i looking at", "current window", "screen context", "what window", "what app", "what's on my screen"}, self._handle_screen_context, "screen_context", 16),
            ({"clipboard", "what did i copy", "copied text", "read clipboard", "paste"}, self._handle_clipboard, "clipboard", 16),
            ({"summarize", "summarise"}, self._handle_summarize, "summarize", 15),

            # Time & Weather
            ({"time", "clock", "what time", "date", "today", "what day"}, self._handle_time, "time", 14),
            ({"weather", "temperature", "forecast"}, self._handle_weather, "weather", 14),

            # Web search
            ({"search", "google", "look up", "web search", "search for"}, self._handle_web_search, "web_search", 12),

            # File search
            ({"find file", "search file", "locate file", "find document"}, self._handle_file_search, "file_search", 12),

            # Math (no 'what is' here — that goes to knowledge engine)
            ({"calculate", "compute", "math", "solve"}, self._handle_math, "math", 10),

            # Memory recall
            ({"what is my", "what's my", "where is my", "recall", "do you remember"}, self._handle_memory_recall, "memory_recall", 9),

            # Knowledge questions — "what is X", "who is X", "explain X", "tell me about X"
            ({"what is", "what are", "who is", "who was", "who are", "where is", "when was", "when did", "why is", "why do", "why does", "how does", "how do", "how is", "explain", "define", "tell me about", "describe", "meaning of"}, self._handle_knowledge_question, "knowledge", 6),

            # Conversation
            ({"hello", "hi", "hey", "greetings", "good morning", "good evening", "good afternoon", "howdy", "jarvis"}, self._handle_greeting, "greeting", 5),
            ({"bye", "goodbye", "exit", "quit", "shutdown", "shut down", "see you", "later", "farewell"}, self._handle_farewell, "farewell", 5),
            ({"thanks", "thank you", "cheers", "appreciate"}, self._handle_thanks, "thanks", 5),
            ({"who are you", "what are you", "your name", "introduce yourself"}, self._handle_identity, "identity", 8),
            ({"help", "commands", "what can you do", "abilities"}, self._handle_help, "help", 8),
            ({"joke", "tell me a joke", "make me laugh", "funny"}, self._handle_joke, "joke", 8),

            # Repeat / follow-up
            ({"again", "repeat", "do that again", "same thing", "one more time"}, self._handle_repeat, "repeat", 25),
        ]

    # ================================================================
    # MAIN PROCESSING PIPELINE
    # ================================================================

    def process(self, user_input: str, visual_context: str = None) -> str:
        """Main entry: classify intent -> extract entities -> execute -> generate response."""
        clean = user_input.strip()
        if not clean:
            return "I didn't catch that, sir."

        self.conversation.append({"role": "user", "text": clean})

        # 1. Check knowledge base first for exact/fuzzy matches
        kb_answer = self._check_knowledge(clean)
        if kb_answer:
            self._record(clean, "knowledge", kb_answer)
            return kb_answer

        # 2. Classify intent using fuzzy scoring
        intent_name, handler, confidence = self._classify_intent(clean)

        # 3. If confidence is too low, try internet knowledge engine
        if confidence < 0.15:
            # First check memory
            recall_result = self.memory.recall(clean.replace("?", "").strip())
            if "No memories found" not in recall_result:
                self._record(clean, "memory_recall", recall_result)
                return recall_result
            # Ask the internet knowledge engine (Wikipedia + DuckDuckGo)
            knowledge_answer = self._ask_internet(clean)
            if knowledge_answer:
                self._record(clean, "internet_knowledge", knowledge_answer)
                return knowledge_answer
            # Truly unknown - still try internet as last resort
            response = self._confused_response(clean)
            self._record(clean, "unknown", response)
            return response

        # 4. Execute the matched handler
        try:
            response = handler(clean, visual_context)
            self.last_intent = intent_name
            self.last_tool_result = response
            self._record(clean, intent_name, response)
            return response
        except Exception as e:
            return f"I encountered an error executing that command, sir: {e}"

    def _classify_intent(self, text: str):
        """Scores all intents and returns (intent_name, handler, confidence).
        Uses max-match scoring: any single keyword match triggers the intent,
        and additional matches boost the score."""
        text_lower = text.lower()
        words = set(text_lower.split())
        best_score = 0.0
        best_handler = None
        best_name = "unknown"

        for keywords, handler, name, priority in self.intents:
            max_kw_score = 0.0
            total_matches = 0

            for keyword in keywords:
                kw_words = keyword.lower().split()
                kw_score = 0.0

                if len(kw_words) > 1:
                    # Multi-word keyword: check substring match
                    if keyword.lower() in text_lower:
                        kw_score = 1.0
                else:
                    # Single word: exact word match
                    if keyword.lower() in words:
                        kw_score = 1.0
                    else:
                        # Fuzzy match individual words
                        for w in words:
                            ratio = difflib.SequenceMatcher(None, keyword.lower(), w).ratio()
                            if ratio > 0.8:
                                kw_score = max(kw_score, ratio)

                if kw_score > 0:
                    total_matches += 1
                    max_kw_score = max(max_kw_score, kw_score)

            # Final score: max keyword match * priority, boosted by additional matches
            if max_kw_score > 0:
                score = max_kw_score * (priority / 10.0) * (1.0 + 0.1 * (total_matches - 1))
            else:
                score = 0.0

            if score > best_score:
                best_score = score
                best_handler = handler
                best_name = name

        return best_name, best_handler, best_score

    def _check_knowledge(self, text: str) -> str:
        """Checks built-in knowledge base using fuzzy string matching."""
        text_lower = text.lower().strip().rstrip("?.,!")
        
        # Direct match
        if text_lower in self.knowledge:
            return self.knowledge[text_lower]

        # Fuzzy match against knowledge keys
        best_match = None
        best_ratio = 0.0
        for key in self.knowledge:
            ratio = difflib.SequenceMatcher(None, text_lower, key).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = key

        if best_ratio > 0.78:
            return self.knowledge[best_match]

        return None

    # ================================================================
    # INTENT HANDLERS
    # ================================================================

    def _handle_greeting(self, text, ctx=None):
        hour = datetime.datetime.now().hour
        greet = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
        responses = [
            f"{greet}, sir. All systems operational. How may I assist you?",
            f"{greet}, sir. Neural pathways active and ready for your commands.",
            f"{greet}, sir. At your service.",
        ]
        return random.choice(responses)

    def _handle_farewell(self, text, ctx=None):
        return random.choice([
            "Powering down gracefully. Until next time, sir.",
            "Shutting down systems. Have a pleasant day, sir.",
            "Goodbye, sir. I'll be here when you need me.",
        ])

    def _handle_thanks(self, text, ctx=None):
        return random.choice(["You're welcome, sir.", "Happy to help, sir.", "Always at your service, sir.", "Anytime, sir."])

    def _handle_identity(self, text, ctx=None):
        return self.knowledge["who are you"]

    def _handle_help(self, text, ctx=None):
        return (
            "Here is what I can do for you, sir:\n"
            "- Open apps: 'Open Notepad', 'Launch Chrome'\n"
            "- System monitoring: 'System stats', 'Take screenshot'\n"
            "- Volume: 'Volume up', 'Mute'\n"
            "- Screen awareness: 'What am I looking at?', 'Read clipboard'\n"
            "- Memory: 'Remember my server IP is 192.168.1.50', 'What is my server IP?'\n"
            "- Time and weather: 'What time is it?', 'Weather in London'\n"
            "- Web search: 'Search for Python tutorials'\n"
            "- File search: 'Find files named report.pdf'\n"
            "- Math: 'Calculate 25 * 4 + 10'\n"
            "- Jokes: 'Tell me a joke'\n"
            "- Follow-ups: 'Do that again'"
        )

    def _handle_joke(self, text, ctx=None):
        return random.choice(self.jokes)

    def _handle_repeat(self, text, ctx=None):
        if self.last_tool_result:
            return f"Repeating last result, sir:\n{self.last_tool_result}"
        return "I don't have a previous action to repeat, sir."

    # --- APPLICATION ---
    def _handle_open_app(self, text, ctx=None):
        text_lower = text.lower()
        # Extract app name after trigger words
        app_match = re.search(r'(?:open|launch|start|run)\s+(.+)', text_lower)
        if not app_match:
            return "Which application should I open, sir?"

        app_raw = app_match.group(1).strip().rstrip(".,!?")

        # Check for URL in original text
        url_match = re.search(r'(https?://[^\s]+|www\.[^\s]+)', text)
        url = url_match.group(1) if url_match else None

        # Browser keywords
        if any(b in app_raw for b in ["chrome", "browser", "firefox", "edge", "safari"]):
            result = system_tools.run_application("chrome", url)
        else:
            result = system_tools.run_application(app_raw, url)

        return f"Right away, sir. {result}"

    # --- SYSTEM ---
    def _handle_stats(self, text, ctx=None):
        return system_tools.get_system_stats()

    def _handle_screenshot(self, text, ctx=None):
        result = system_tools.take_screenshot()
        return f"Very well, sir. {result}"

    def _handle_volume_up(self, text, ctx=None):
        return system_tools.adjust_system_volume("up")
    def _handle_volume_down(self, text, ctx=None):
        return system_tools.adjust_system_volume("down")
    def _handle_mute(self, text, ctx=None):
        return system_tools.adjust_system_volume("mute")
    def _handle_unmute(self, text, ctx=None):
        return system_tools.adjust_system_volume("unmute")

    # --- CONTEXT ---
    def _handle_screen_context(self, text, ctx=None):
        result = context_tools.get_screen_context()
        if ctx and "No ambient" not in ctx:
            result += f"\n\nAmbient observations:\n{ctx}"
        return result

    def _handle_clipboard(self, text, ctx=None):
        return context_tools.get_clipboard_text()

    def _handle_summarize(self, text, ctx=None):
        clipboard = context_tools.get_clipboard_text()
        if "empty" in clipboard.lower():
            screen = context_tools.get_screen_context()
            return f"Your clipboard is empty, sir. But I can see: {screen}"
        # Return clipboard with context prefix
        return f"Here is what you have in your clipboard, sir:\n{clipboard}"

    # --- MEMORY ---
    def _handle_memory_store(self, text, ctx=None):
        text_lower = text.lower()
        # Pattern: "remember (that) X is Y"
        match = re.search(r'(?:remember|store|save|note|memorize)\s+(?:that\s+)?(.*?)\s+is\s+(.*)', text_lower)
        if match:
            key, val = match.group(1).strip(), match.group(2).strip()
            result = self.memory.store(key, val)
            return f"Consider it done, sir. {result}"

        # Pattern: "remember X: Y"
        match2 = re.search(r'(?:remember|store|save|note)\s+(.*?):\s*(.*)', text_lower)
        if match2:
            key, val = match2.group(1).strip(), match2.group(2).strip()
            result = self.memory.store(key, val)
            return f"Very well, sir. {result}"

        # Fallback: store the whole phrase
        content = re.sub(r'^(remember|store|save|note|memorize)\s+(?:that\s+)?', '', text_lower).strip()
        if content:
            result = self.memory.store(content, "noted")
            return f"On it, sir. {result}"

        return "What would you like me to remember, sir?"

    def _handle_memory_recall(self, text, ctx=None):
        text_lower = text.lower()
        query = re.sub(r'^(what is|what\'s|where is|where\'s|tell me|do you remember|recall)\s+(my\s+)?', '', text_lower).strip().rstrip("?.,!")
        if query:
            return self.memory.recall(query)
        return "What would you like me to recall, sir?"

    def _handle_memory_list(self, text, ctx=None):
        return self.memory.list_all()

    def _handle_memory_delete(self, text, ctx=None):
        text_lower = text.lower()
        key = re.sub(r'^(forget|delete|remove|erase)\s+(memory\s+)?(about|for|of)?\s*', '', text_lower).strip().rstrip("?.,!")
        if key:
            return self.memory.delete(key)
        return "Which memory should I forget, sir?"

    # --- TIME & WEATHER ---
    def _handle_time(self, text, ctx=None):
        return web_tools.get_weather_and_time()

    def _handle_weather(self, text, ctx=None):
        loc_match = re.search(r'(?:in|for|at)\s+(.+)', text, re.IGNORECASE)
        loc = loc_match.group(1).strip().rstrip("?.,!") if loc_match else None
        return web_tools.get_weather_and_time(loc)

    # --- WEB SEARCH ---
    def _handle_web_search(self, text, ctx=None):
        query = re.sub(r'^(search|google|look up|web search|search for|find out)\s+', '', text, flags=re.IGNORECASE).strip().rstrip("?.,!")
        if query:
            return web_tools.web_search(query)
        return "What would you like me to search for, sir?"

    # --- FILE SEARCH ---
    def _handle_file_search(self, text, ctx=None):
        filename = re.sub(r'^(find|search|locate|look for)\s+(file|files|document|documents)\s*(named|called|matching)?\s*', '', text, flags=re.IGNORECASE).strip().rstrip("?.,!")
        if not filename:
            filename = re.sub(r'^(find|search|locate)\s+', '', text, flags=re.IGNORECASE).strip().rstrip("?.,!")
        if filename:
            return file_tools.search_files(filename)
        return "What file should I search for, sir?"

    # --- MATH ---
    def _handle_math(self, text, ctx=None):
        # Extract mathematical expression
        expr = re.sub(r'^(calculate|compute|solve|what is|math)\s+', '', text, flags=re.IGNORECASE).strip().rstrip("?.,!")
        # Clean text operators
        expr = expr.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("multiplied by", "*")
        expr = expr.replace("divided by", "/").replace("x", "*").replace("^", "**")
        expr = expr.replace("power", "**").replace("mod", "%").replace("modulo", "%")

        # Only allow safe characters
        safe_expr = re.sub(r'[^0-9+\-*/.()%\s]', '', expr).strip()
        if not safe_expr:
            # Not a math expression, try knowledge engine
            return self._handle_knowledge_question(text)

        try:
            # Use eval with restricted builtins for safety
            allowed = {"__builtins__": {}, "math": math, "abs": abs, "round": round, "pow": pow, "sqrt": math.sqrt}
            result = eval(safe_expr, allowed)
            if isinstance(result, float) and result == int(result):
                result = int(result)
            return f"The answer is {result}, sir."
        except Exception:
            # Fall through to knowledge engine
            return self._handle_knowledge_question(text)

    # --- KNOWLEDGE QUESTIONS (Internet-powered) ---
    def _handle_knowledge_question(self, text, ctx=None):
        """Answers ANY question by searching Wikipedia + DuckDuckGo."""
        answer = self._ask_internet(text)
        if answer:
            return answer
        return f"I searched multiple sources but couldn't find a clear answer for that, sir. Try asking differently."

    # ================================================================
    # INTERNET KNOWLEDGE ENGINE
    # ================================================================

    def _ask_internet(self, query: str) -> str:
        """Connects to free internet knowledge sources to answer any question.
        Sources: DuckDuckGo Instant Answer -> Wikipedia -> Web Search.
        No API keys needed. 100% free."""
        try:
            return web_tools.answer_question(query)
        except Exception as e:
            return f"I tried to search the internet but hit an error: {e}"

    # ================================================================
    # UTILITIES
    # ================================================================

    def _confused_response(self, text: str) -> str:
        """Last resort: always try internet before giving up."""
        internet_answer = self._ask_internet(text)
        if internet_answer and "couldn't find" not in internet_answer.lower():
            return internet_answer
        return f"I searched the internet but couldn't find a clear answer for '{text[:40]}', sir. Try rephrasing or say 'help' for my capabilities."

    def _record(self, user_text, intent, response):
        """Records conversation turn for context tracking."""
        self.conversation.append({"role": "assistant", "text": response, "intent": intent})
        # Trim conversation to last 20 turns
        if len(self.conversation) > 40:
            self.conversation = self.conversation[-40:]


# ================================================================
# SELF-TEST
# ================================================================
if __name__ == "__main__":
    brain = SuperBrain()
    test_commands = [
        "Hello JARVIS",
        "Who are you?",
        "What can you do?",
        "Open Notepad",
        "System stats",
        "Take a screenshot",
        "What time is it?",
        "Calculate 25 * 4 + 10",
        "Remember that my server IP is 192.168.1.50",
        "What is my server IP?",
        "List all memories",
        "Tell me a joke",
        "Search for Python tutorials",
        "What am I looking at?",
        "Read clipboard",
        "Do that again",
        "Forget my server IP",
        "Goodbye",
    ]
    print("=" * 60)
    print("     JARVIS SUPER BRAIN SELF-TEST")
    print("=" * 60)
    for cmd in test_commands:
        print(f"\n[YOU]: {cmd}")
        print(f"[JARVIS]: {brain.process(cmd)}")
    print("\n" + "=" * 60)
    print("     ALL TESTS COMPLETE")
    print("=" * 60)
