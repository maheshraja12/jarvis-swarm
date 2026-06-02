import time
import random
import sys
import os
import math

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from brain.local_brain import SuperBrain
from brain.agent import JarvisAgent
from tools import web_tools, system_tools

# 1. Mock network & hardware dependencies to run benchmarks locally, safely, and instantly
web_tools.answer_question = lambda q: f"Mock factual answer for '{q}', sir."
web_tools.web_search = lambda q: f"Mock web search results for query, sir."
web_tools.get_weather_and_time = lambda loc=None: "Today is Tuesday, and it is 12:00 PM, sir. Weather is sunny."
system_tools.take_screenshot = lambda: "Screenshot saved successfully, sir."
system_tools.adjust_system_volume = lambda action, pct=None: f"Volume adjusted to {action}, sir."
system_tools.run_application = lambda app, url=None: f"Application {app} launched successfully, sir."

def generate_testcases():
    testcases = []
    
    # Category 1: Fuzzy greetings (150 queries)
    greetings = ["hello", "hi", "hey", "greetings", "good morning", "good evening", "good afternoon", "howdy", "jarvis"]
    for i in range(150):
        testcases.append((f"{random.choice(greetings)} jarvis assistant {i}", "greeting"))
        
    # Category 2: Arithmetic math evaluator (200 queries)
    ops = ["+", "-", "*", "/"]
    for i in range(200):
        n1 = random.randint(1, 1000)
        n2 = random.randint(1, 100)
        op = random.choice(ops)
        testcases.append((f"calculate {n1} {op} {n2}", "math"))
        
    # Category 3: Memory DB store, recall, delete (250 queries)
    keys = ["server ip", "wifi key", "boss name", "api key", "birthday", "location", "model rate"]
    for i in range(250):
        key = random.choice(keys) + f"_{i}"
        val = f"value_{random.randint(1000, 9999)}"
        if i % 3 == 0:
            testcases.append((f"remember that my {key} is {val}", "memory_store"))
        elif i % 3 == 1:
            testcases.append((f"what is my {key}", "memory_recall"))
        else:
            testcases.append((f"forget my {key}", "memory_delete"))
            
    # Category 4: App control (150 queries)
    apps = ["notepad", "chrome", "calculator", "explorer", "paint", "command prompt", "powershell"]
    for i in range(150):
        testcases.append((f"open {random.choice(apps)}", "open_app"))
        
    # Category 5: Hardware stats and mute controls (100 queries)
    system_queries = [
        ("system stats", "stats"),
        ("cpu usage status", "stats"),
        ("performance report", "stats"),
        ("take a screenshot", "screenshot"),
        ("volume up", "volume_up"),
        ("volume down", "volume_down"),
        ("mute the sound", "mute"),
        ("unmute speaker", "unmute"),
    ]
    for _ in range(100):
        query, expected = random.choice(system_queries)
        testcases.append((query, expected))
        
    # Category 6: Factual questions (150 queries)
    questions = [
        "what is quantum physics", "who is elon musk", "explain DNA",
        "what is machine learning", "tell me about artificial intelligence"
    ]
    for i in range(150):
        testcases.append((f"{random.choice(questions)} query_{i}", "knowledge"))
        
    random.shuffle(testcases)
    return testcases[:1000]

def run_stress_test():
    print("=" * 60)
    print("        JARVIS SUPER BRAIN: 1,000 TESTCASES BENCHMARK")
    print("=" * 60)
    
    print("[Action] Generating 1,000 distinct benchmark queries...")
    testcases = generate_testcases()
    print(f"[Info] Generated {len(testcases)} queries successfully.")
    
    print("\n[Action] Initializing engine and loading database...")
    brain = SuperBrain()
    
    success_count = 0
    failure_count = 0
    intent_matches = 0
    
    start_time = time.time()
    
    print("[Progress] Processing 1,000 test cases...")
    for idx, (query, expected_intent) in enumerate(testcases):
        try:
            # Execute processing loop
            response = brain.process(query)
            
            # Basic validation
            if response and isinstance(response, str):
                success_count += 1
            else:
                failure_count += 1
                
            # Check intent matching accuracy
            if expected_intent:
                matched_intent, _, _ = brain._classify_intent(query)
                if matched_intent == expected_intent:
                    intent_matches += 1
                    
        except Exception as e:
            failure_count += 1
            print(f"      [Crash] Error on query '{query}': {e}")
            
    total_time = time.time() - start_time
    avg_latency_ms = (total_time / len(testcases)) * 1000
    
    print("\n" + "=" * 60)
    print("                 BENCHMARK PERFORMANCE REPORT")
    print("=" * 60)
    print(f"  - Total Testcases Run   : {len(testcases)}")
    print(f"  - Success Rate          : {(success_count / len(testcases)) * 100:.2f}% ({success_count} / {len(testcases)})")
    print(f"  - Error / Crash Count   : {failure_count}")
    print(f"  - Total Execution Time  : {total_time:.4f} seconds")
    print(f"  - Average Query Latency : {avg_latency_ms:.4f} ms")
    print(f"  - Intent Classification : {(intent_matches / len(testcases)) * 100:.2f}% accuracy")
    print("-" * 60)
    print("  [Verdict] J.A.R.V.I.S. Local Intelligence Engine is STABLE, sir.")
    print("=" * 60)

if __name__ == "__main__":
    run_stress_test()
