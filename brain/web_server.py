from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import sys
import psutil
import asyncio

# Add parent directory to path to allow importing sibling modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from brain.agent import JarvisAgent
from brain.memory import JarvisMemory

app = FastAPI(title="J.A.R.V.I.S. Swarm API")

# Mount Static Files to serve the HUD frontend
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Shared state indicators
class SwarmState:
    audio_status = "standby"  # standby, listening, speaking, thinking
    swarm_actor_state = "standby"  # standby, orchestrating, coding, critiquing
    visual_buffer_ref = None
    agent_ref = None

# Base Models
class CommandRequest(BaseModel):
    command: str

@app.get("/api/status")
def get_status():
    """Returns real-time hardware performance and swarm status telemetry."""
    # Hardware Stats
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    
    battery_charge = 100
    power_plugged = True
    battery = psutil.sensors_battery()
    if battery:
        battery_charge = battery.percent
        power_plugged = battery.power_plugged

    # Dynamic Custom Tools Count
    custom_tools_count = 0
    if SwarmState.agent_ref and SwarmState.agent_ref.custom_manager:
        custom_tools_count = len(SwarmState.agent_ref.custom_manager.custom_tools)

    return {
        "cpu": cpu,
        "ram": ram,
        "battery": {
            "charge": battery_charge,
            "plugged": power_plugged
        },
        "audio_status": SwarmState.audio_status,
        "swarm_state": SwarmState.swarm_actor_state,
        "custom_tools_count": custom_tools_count
    }

@app.get("/api/memory")
def get_memories():
    """Lists all memories stored in the SQLite database."""
    try:
        memory = JarvisMemory()
        conn = memory.sqlite3.connect(memory.db_path) if hasattr(memory, 'sqlite3') else None
        # Let's import sqlite3 directly to guarantee execution
        import sqlite3
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM memories")
        rows = cursor.fetchall()
        conn.close()
        
        mem_dict = {key: val for key, val in rows}
        return {"memories": mem_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/memory/{key}")
def delete_memory(key: str):
    """Deletes a fact from long-term memory."""
    try:
        memory = JarvisMemory()
        res = memory.delete(key)
        if "No memory key" in res:
            raise HTTPException(status_code=404, detail=res)
        return {"status": "success", "message": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tools")
def get_tools():
    """Lists built-in and dynamically created custom tool schemas."""
    custom_tools = []
    if SwarmState.agent_ref and SwarmState.agent_ref.custom_manager:
        schemas = SwarmState.agent_ref.custom_manager.get_tool_schemas()
        for s in schemas:
            func = s.get("function", {})
            custom_tools.append({
                "name": func.get("name"),
                "description": func.get("description")
            })
    return {"custom_tools": custom_tools}

@app.post("/api/command")
async def execute_command(req: CommandRequest):
    """Executes manual text commands through the Swarm agent."""
    if not SwarmState.agent_ref:
        raise HTTPException(status_code=503, detail="Agent engine is initializing...")
        
    cmd = req.command.strip()
    if not cmd:
        raise HTTPException(status_code=400, detail="Command cannot be empty")

    # Get visual buffer context
    visual_context = None
    if SwarmState.visual_buffer_ref:
        visual_context = SwarmState.visual_buffer_ref.get_context_summary()

    # 1. Update state to Thinking/Speaking
    SwarmState.audio_status = "thinking"
    
    # Track swarm state based on keywords
    if "tool" in cmd.lower() or "create" in cmd.lower():
        SwarmState.swarm_actor_state = "coding"
    else:
        SwarmState.swarm_actor_state = "orchestrating"

    # 2. Run agent chat
    try:
        response_text = await SwarmState.agent_ref.chat(cmd, visual_context=visual_context)
        
        # Determine if speak synthesis should run (async background read-out simulation)
        SwarmState.audio_status = "speaking"
        
        # Reset swarm states back to standby
        SwarmState.swarm_actor_state = "standby"
        
        # We spawn a background task to speak the text using pyttsx3/edge-tts without blocking the HTTP response
        # Using a slight delay to allow client to transition state
        asyncio.create_task(speak_response_delayed(response_text))
        
        return {"response": response_text}
    except Exception as e:
        SwarmState.audio_status = "standby"
        SwarmState.swarm_actor_state = "standby"
        raise HTTPException(status_code=500, detail=f"Engine execution failure: {e}")

async def speak_response_delayed(text: str):
    """Speaks the response using speaker helper after a brief state delay."""
    await asyncio.sleep(0.3)
    from io_dev.audio_output import JarvisSpeaker
    try:
        speaker = JarvisSpeaker()
        await speaker.speak(text)
    except Exception:
        pass
    SwarmState.audio_status = "standby"

@app.get("/")
def read_root():
    """Redirects to static HUD dashboard file."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")
