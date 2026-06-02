"""
JARVIS Web Tools & Knowledge Engine
====================================
Connects to FREE public internet knowledge sources (no API keys needed):
  - Wikipedia API: instant factual answers
  - DuckDuckGo Instant Answer API: quick definitions & facts
  - DuckDuckGo HTML Search: full web search results
  - wttr.in: weather data
All sources are 100% free, no sign-up, no API keys.
"""

import requests
import re
import datetime
import urllib.parse
import json


# ================================================================
# 1. WIKIPEDIA KNOWLEDGE ENGINE (Free, no API key)
# ================================================================

def ask_wikipedia(query: str) -> str:
    """Fetches a concise summary from Wikipedia for any knowledge question.
    Uses the Wikipedia REST API - free, no key required."""
    query = query.strip()
    if not query:
        return ""

    # Clean question words to get the actual search topic
    clean = re.sub(
        r'^(what is|what are|what was|who is|who are|who was|where is|where are|'
        r'when was|when did|when is|why is|why do|why does|how does|how do|how is|'
        r'explain|define|tell me about|describe|meaning of|the meaning of)\s+',
        '', query, flags=re.IGNORECASE
    ).strip().rstrip("?.,!")

    # Handle "capital of X" -> search "X capital"
    cap_match = re.match(r'(?:the\s+)?capital\s+of\s+(.+)', clean, re.IGNORECASE)
    if cap_match:
        clean = cap_match.group(1).strip()
        # Search directly for the country
        clean = clean + " country"

    if not clean:
        clean = query.strip().rstrip("?.,!")

    headers = {
        "User-Agent": "JARVIS-Assistant/3.0 (local; personal use)"
    }

    try:
        # Step 1: Search Wikipedia for the best matching articles (top 3)
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": clean,
            "srlimit": 3,
            "format": "json",
        }
        search_resp = requests.get(search_url, params=search_params, headers=headers, timeout=8)
        if search_resp.status_code != 200:
            return ""

        search_data = search_resp.json()
        results = search_data.get("query", {}).get("search", [])
        if not results:
            return ""

        # Pick the best matching title
        clean_lower = clean.lower()
        best_title = results[0]["title"]
        best_score = 0
        for r in results:
            title_lower = r["title"].lower()
            # Prefer exact or close title match
            if clean_lower == title_lower:
                best_title = r["title"]
                break
            # Score by word overlap
            title_words = set(title_lower.split())
            query_words = set(clean_lower.split())
            overlap = len(title_words & query_words)
            if overlap > best_score:
                best_score = overlap
                best_title = r["title"]

        # Step 2: Get the article summary using the REST API
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(best_title)}"
        summary_resp = requests.get(summary_url, headers=headers, timeout=8)
        if summary_resp.status_code != 200:
            return ""

        summary_data = summary_resp.json()
        extract = summary_data.get("extract", "")

        if extract:
            # Trim to a reasonable length for speech
            sentences = extract.split(". ")
            short = ". ".join(sentences[:4])
            if not short.endswith("."):
                short += "."
            # Clean non-ASCII for Windows console
            short = short.encode('ascii', 'replace').decode('ascii')
            return f"According to Wikipedia, sir:\n{short}"

        return ""

    except Exception:
        return ""


# ================================================================
# 2. DUCKDUCKGO INSTANT ANSWER (Free, no API key)
# ================================================================

def ask_instant_answer(query: str) -> str:
    """Uses DuckDuckGo's Instant Answer API for quick factual responses.
    Free, no API key, returns definitions, facts, and summaries."""
    query = query.strip()
    if not query:
        return ""

    # Clean question words to get the actual search topic
    clean = re.sub(
        r'^(what is|what are|what was|who is|who are|who was|where is|where are|'
        r'when was|when did|when is|why is|why do|why does|how does|how do|how is|'
        r'explain|define|tell me about|describe|meaning of|the meaning of)\s+',
        '', query, flags=re.IGNORECASE
    ).strip().rstrip("?.,!")

    if not clean:
        clean = query.strip().rstrip("?.,!")

    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": clean,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        resp = requests.get(url, params=params, timeout=8)
        if resp.status_code != 200:
            return ""

        data = resp.json()

        # Check Abstract (best quality answer)
        abstract = data.get("AbstractText", "").strip()
        if abstract:
            sentences = abstract.split(". ")
            short = ". ".join(sentences[:4])
            if not short.endswith("."):
                short += "."
            short = short.encode('ascii', 'replace').decode('ascii')
            source = data.get("AbstractSource", "")
            return f"Here's what I found, sir:\n{short}" + (f"\n(Source: {source})" if source else "")

        # Check Answer field (direct factual answer)
        answer = data.get("Answer", "").strip()
        if answer:
            answer = answer.encode('ascii', 'replace').decode('ascii')
            return f"The answer is: {answer}, sir."

        # Check Definition
        definition = data.get("Definition", "").strip()
        if definition:
            definition = definition.encode('ascii', 'replace').decode('ascii')
            return f"Definition: {definition}, sir."

        # Check Related Topics for a quick snippet
        related = data.get("RelatedTopics", [])
        if related and isinstance(related[0], dict):
            text = related[0].get("Text", "").strip()
            if text:
                text = text.encode('ascii', 'replace').decode('ascii')
                return f"Here's what I found, sir:\n{text}"

        return ""

    except Exception:
        return ""


# ================================================================
# 3. UNIFIED KNOWLEDGE QUERY (tries all sources)
# ================================================================

def answer_question(query: str) -> str:
    """Tries multiple free knowledge sources to answer any question.
    Order: DuckDuckGo Instant -> Wikipedia -> DuckDuckGo Web Search."""
    clean_query = query.strip().rstrip("?.,!")
    if not clean_query:
        return "What would you like to know, sir?"

    # Source 1: DuckDuckGo Instant Answer (fastest)
    answer = ask_instant_answer(clean_query)
    if answer:
        return answer

    # Source 2: Wikipedia (most detailed)
    answer = ask_wikipedia(clean_query)
    if answer:
        return answer

    # Source 3: Full web search (broadest)
    answer = web_search(clean_query)
    if answer and "could not extract" not in answer.lower():
        return answer

    return f"I searched multiple sources for '{clean_query}' but couldn't find a clear answer, sir. Try rephrasing your question."


# ================================================================
# 4. WEB SEARCH (DuckDuckGo HTML)
# ================================================================

def web_search(query: str) -> str:
    """Performs a web lookup on DuckDuckGo and returns search snippet results."""
    query = query.strip()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Use DuckDuckGo HTML search
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return f"Search service returned status code {response.status_code}, sir."

        html = response.text

        results = []

        blocks = re.findall(r'<div class="web-result.*?">(.*?)</div>\s*</div>', html, re.DOTALL)
        if not blocks:
            snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
            titles = re.findall(r'<a class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)

            for t, s in zip(titles[:5], snippets[:5]):
                t_clean = re.sub(r'<[^>]+>', '', t).strip()
                s_clean = re.sub(r'<[^>]+>', '', s).strip()
                if t_clean and s_clean:
                    results.append(f"- {t_clean}: {s_clean}")
        else:
            for block in blocks[:5]:
                title_match = re.search(r'<a class="result__a"[^>]*>(.*?)</a>', block, re.DOTALL)
                snippet_match = re.search(r'<a class="result__snippet"[^>]*>(.*?)</a>', block, re.DOTALL)

                if title_match and snippet_match:
                    t = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                    s = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
                    if t and s:
                        results.append(f"- {t}: {s}")

        if not results:
            return f"I performed a search for '{query}' but could not extract any relevant results, sir."

        summary = f"Search results for '{query}':\n" + "\n".join(results)
        return summary
    except Exception as e:
        return f"Failed to perform search: {e}"


# ================================================================
# 5. WEATHER & TIME
# ================================================================

def get_weather_and_time(location: str = None) -> str:
    """Returns local time and fetches weather using wttr.in."""
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%A, %B %d, %Y")

    status = f"Today is {date_str}, and the time is {time_str}, sir."

    loc_query = location.strip() if location else ""

    try:
        url = f"https://wttr.in/{loc_query}?format=3"
        weather_res = requests.get(url, timeout=5)
        if weather_res.status_code == 200:
            weather_text = weather_res.text.strip()
            # Strip non-ASCII emoji to avoid Windows console encoding errors
            weather_text = weather_text.encode('ascii', 'ignore').decode('ascii').strip()
            if weather_text and "weather report" not in weather_text.lower() and "error" not in weather_text.lower():
                status += f"\nWeather status: {weather_text}."
            else:
                status += "\nI was unable to retrieve the weather report at this time."
        else:
            status += "\nI was unable to connect to the weather service."
    except Exception as e:
        status += f"\n(Weather lookup failed: {e})"

    return status


# ================================================================
# SELF-TEST
# ================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("     JARVIS KNOWLEDGE ENGINE SELF-TEST")
    print("=" * 60)

    tests = [
        "What is quantum physics",
        "Who is Elon Musk",
        "What is Python programming language",
        "Capital of Japan",
        "Who invented the telephone",
    ]

    for q in tests:
        print(f"\n[QUESTION]: {q}")
        print(f"[ANSWER]: {answer_question(q)}")

    print(f"\n[TIME/WEATHER]:\n{get_weather_and_time()}")
    print("\n" + "=" * 60)
