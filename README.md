# JARVIS Swarm

JARVIS is a local-first personal voice assistant with a FastAPI HUD, agent tools, and long-term memory.

## Run locally

1. Use Python 3.11 or newer and create a virtual environment.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Review `config.py` and choose the brain mode you want. Do not commit API keys or other secrets.
4. Start the assistant with `python main.py`. The bundled HUD is served at `http://127.0.0.1:8000` when the web server is enabled.

The built-in server binds to loopback by default. Keep it local unless you have deliberately configured and reviewed remote access.

## API security

- `/api/command`, `/api/memory`, and `/api/memory/{key}` are sensitive because they can trigger agent actions or expose/delete stored memories.
- Loopback requests are permitted for the local HUD. Requests from non-loopback clients fail closed unless `JARVIS_API_TOKEN` is configured.
- For remote clients, set a strong random `JARVIS_API_TOKEN` in the server environment and send it as the `X-JARVIS-Token` request header. Never put the token in frontend JavaScript, a public repository, or a URL.
- Set `JARVIS_ALLOWED_ORIGINS` to a comma-separated allowlist of exact trusted origins if a remote browser client is required. CORS is not authentication; keep network/firewall access restricted as well.
- The bundled HUD is designed for local loopback use. Remote browser integration needs a secure token-forwarding design rather than embedding a secret in static files.
- API errors avoid returning raw internal exceptions or local paths.

Example environment setup (Linux/macOS shell):

```sh
export JARVIS_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export JARVIS_ALLOWED_ORIGINS="http://localhost:8000,http://127.0.0.1:8000"
python main.py
```

When a token is configured, it protects sensitive endpoints for remote clients. Local loopback calls continue to work without the token so the local HUD remains usable.

## Tests

Run the non-hardware-dependent test suite:

```sh
python -m pip install pytest httpx fastapi psutil requests
pytest -q tests
```

CI compiles the Python modules and runs these safe tests. This is not a certification of hardware-specific audio, desktop automation, or remote deployment security.
