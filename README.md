# JARVIS Swarm

JARVIS is a local-first personal voice assistant with a FastAPI HUD, agent tools, and long-term memory.

## Run locally

**Windows:** double-click `start_jarvis.bat` or run it from Command Prompt.
**Linux/macOS:** run `bash start_jarvis.sh`.

The scripts create a virtual environment, install dependencies, and copy `.env.example` to `.env` if needed. Edit `.env` to choose the brain and trigger mode, then restart JARVIS. Python 3.11 or newer is required. On Linux, audio support may require OS packages for PortAudio and a working desktop audio stack.

For manual setup:

1. Create and activate a Python virtual environment.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`; do not commit secrets.
4. Start with `python main.py`. The bundled HUD is served at `http://127.0.0.1:8000` when enabled.

The built-in server binds to loopback by default. Keep it local unless you have deliberately configured and reviewed remote access.

## API security

- All `/api/*` routes are protected from non-loopback clients because they may expose local telemetry, tool metadata, memories, or agent actions.
- Loopback requests are permitted for the local HUD. Requests to all `/api/*` routes from non-loopback clients fail closed unless `JARVIS_API_TOKEN` is configured.
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

When a token is configured, it protects all API routes for remote clients. Local loopback calls continue to work without the token so the local HUD remains usable.

## Custom Python tools

Dynamic custom tools are **disabled by default**. JARVIS currently imports custom Python modules into its own process; syntax compilation is not a sandbox, and imported code can access the same files, credentials, network, and operating-system permissions as JARVIS.

Only if you have reviewed and trust every custom tool, you can explicitly opt in by setting:

```sh
export JARVIS_ENABLE_UNSAFE_CUSTOM_TOOLS=1
```

Restart JARVIS after changing the setting. Do not enable this option for untrusted model-generated code or on a machine holding sensitive credentials. A true security boundary requires a separate restricted process/container with filesystem, network, CPU, and memory controls; this repository does not yet provide that boundary.

## Tests

Run the non-hardware-dependent test suite:

```sh
python -m pip install pytest httpx fastapi psutil requests
pytest -q tests
```

CI compiles the Python modules and runs safe unit tests. A minimal `/health` endpoint is available for local supervision. This remains a **local desktop application**, not a cloud-hosted microphone/screen-control service; microphone, speakers, keyboard hooks, and desktop automation must be tested on the target computer. The scripts are deployment helpers, not proof that hardware-specific features work on every machine.
