"""Local JARVIS HUD API with safe defaults for remotely exposed deployments."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import hmac
import os
import psutil
import sqlite3
import sys

# Add parent directory to path to allow importing sibling modules.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

app = FastAPI(title="J.A.R.V.I.S. Swarm API")

_DEFAULT_ORIGINS = (
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)
_allowed_origins = [
    origin.strip()
    for origin in os.getenv("JARVIS_ALLOWED_ORIGINS", ",".join(_DEFAULT_ORIGINS)).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-JARVIS-Token", "Authorization"],
)

# Mount static HUD frontend.
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Routes that expose memory or trigger agent actions must not be remotely reachable
# without a configured shared token. Loopback-only local use remains convenient.
_SENSITIVE_PATHS = ("/api/command", "/api/memory")


class SwarmState:
    audio_status = "standby"  # standby, listening, speaking, thinking
    swarm_actor_state = "standby"  # standby, orchestrating, coding, critiquing
    visual_buffer_ref = None
    agent_ref = None


class CommandRequest(BaseModel):
    command: str


def _is_loopback(request: Request) -> bool:
    host = request.client.host if request.client else ""
    return host in {"127.0.0.1", "::1", "localhost", "testclient"}


@app.middleware("http")
async def protect_sensitive_routes(request: Request, call_next):
    path = request.url.path
    sensitive = path == "/api/command" or path == "/api/memory" or path.startswith("/api/memory/")
    if sensitive and request.method in {"GET", "POST", "DELETE", "PUT", "PATCH"}:
        expected = os.getenv("JARVIS_API_TOKEN", "").strip()
        supplied = request.headers.get("X-JARVIS-Token", "")
        if expected:
            if not supplied or not hmac.compare_digest(supplied, expected):
                from starlette.responses import JSONResponse
                return JSONResponse(status_code=401, content={"detail": "Valid X-JARVIS-Token header required"})
        elif not _is_loopback(request):
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=503,
                content={"detail": "Remote access to this endpoint is disabled until JARVIS_API_TOKEN is configured"},
            )
    return await call_next(request)


@app.get("/api/status")
def get_status():
    """Returns hardware performance and swarm status telemetry."""
    battery_charge = 100
    power_plugged = True
    battery = psutil.sensors_battery()
    if battery:
        battery_charge = battery.percent
        power_plugged = battery.power_plugged

    custom_tools_count = 0
    if SwarmState.agent_ref and SwarmState.agent_ref.custom_manager:
        custom_tools_count = len(SwarmState.agent_ref.custom_manager.custom_tools)

    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "battery": {"charge": battery_charge, "plugged": power_plugged},
        "audio_status": SwarmState.audio_status,
        "swarm_state": SwarmState.swarm_actor_state,
        "custom_tools_count": custom_tools_count,
    }


@app.get("/api/memory")
def get_memories():
    """Lists memories stored in the SQLite database; route is access-controlled."""
    try:
        with sqlite3.connect(config.DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM memories")
            rows = cursor.fetchall()
        return {"memories": {key: value for key, value in rows}}
    except sqlite3.Error:
        # Avoid returning database paths, SQL details, or internal exceptions to clients.
        raise HTTPException(status_code=500, detail="Memory store is unavailable")


@app.delete("/api/memory/{key}")
def delete_memory(key: str):
    """Deletes a fact from long-term memory; route is access-controlled."""
    try:
        from brain.memory import JarvisMemory
        memory = JarvisMemory()
        result = memory.delete(key)
        if "No memory key" in result:
            raise HTTPException(status_code=404, detail="Memory key not found")
        return {"status": "success", "message": result}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Memory operation failed")


@app.get("/api/tools")
def get_tools():
    """Lists built-in and dynamically created custom tool schemas."""
    custom_tools = []
    if SwarmState.agent_ref and SwarmState.agent_ref.custom_manager:
        for schema in SwarmState.agent_ref.custom_manager.get_tool_schemas():
            func = schema.get("function", {})
            custom_tools.append({"name": func.get("name"), "description": func.get("description")})
    return {"custom_tools": custom_tools}


@app.post("/api/command")
async def execute_command(req: CommandRequest):
    """Executes a manual text command through the Swarm agent; access-controlled."""
    if not SwarmState.agent_ref:
        raise HTTPException(status_code=503, detail="Agent engine is initializing...")

    command = req.command.strip()
    if not command:
        raise HTTPException(status_code=400, detail="Command cannot be empty")

    visual_context = None
    if SwarmState.visual_buffer_ref:
        visual_context = SwarmState.visual_buffer_ref.get_context_summary()

    SwarmState.audio_status = "thinking"
    SwarmState.swarm_actor_state = "coding" if any(
        word in command.lower() for word in ("tool", "create")
    ) else "orchestrating"

    try:
        response_text = await SwarmState.agent_ref.chat(command, visual_context=visual_context)
        SwarmState.audio_status = "speaking"
        SwarmState.swarm_actor_state = "standby"
        asyncio.create_task(speak_response_delayed(response_text))
        return {"response": response_text}
    except Exception:
        SwarmState.audio_status = "standby"
        SwarmState.swarm_actor_state = "standby"
        # Do not leak agent prompts, local paths, or provider errors to API callers.
        raise HTTPException(status_code=500, detail="Agent execution failed")


async def speak_response_delayed(text: str):
    """Speaks a response using the configured speaker helper."""
    await asyncio.sleep(0.3)
    try:
        from io_dev.audio_output import JarvisSpeaker
        speaker = JarvisSpeaker()
        await speaker.speak(text)
    except Exception:
        pass
    finally:
        SwarmState.audio_status = "standby"


@app.get("/")
def read_root():
    """Redirects to the static HUD dashboard file."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")
