import asyncio
import os
import sys
import uvicorn

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from io_dev.audio_output import JarvisSpeaker
from io_dev.audio_input import JarvisListener
from io_dev.visual_buffer import JarvisVisualBuffer
from brain.agent import JarvisAgent
from brain.web_server import app, SwarmState

# Shared event loop reference for thread-safe scheduling
main_loop = None
wake_event = None
keyboard_triggered = False

def on_hotkey_pressed():
    """Callback fired when the keyboard hotkey is pressed."""
    global keyboard_triggered
    if main_loop and wake_event:
        print("\n[Hotkey Triggered] Keyboard hotkey pressed, waking up...")
        keyboard_triggered = True
        main_loop.call_soon_threadsafe(wake_event.set)

def setup_keyboard_hotkey():
    """Attempts to set up the keyboard shortcut trigger."""
    if config.TRIGGER_MODE in ["keyboard", "hybrid"]:
        try:
            import keyboard
            keyboard.add_hotkey(config.HOTKEY_TRIGGER, on_hotkey_pressed)
            print(f"[Main System] Keyboard hotkey trigger active. Press '{config.HOTKEY_TRIGGER}' to talk.")
        except Exception as e:
            print(f"[Main System Warning] Could not register keyboard shortcut: {e}")

async def process_user_command(agent: JarvisAgent, speaker: JarvisSpeaker, listener: JarvisListener, visual_buffer: JarvisVisualBuffer, transcribed_text: str):
    """Processes a transcribed command through the brain agent and speaks the response."""
    if not transcribed_text:
        SwarmState.audio_status = "standby"
        SwarmState.swarm_actor_state = "standby"
        return
        
    SwarmState.audio_status = "thinking"
    
    # Identify swarm actor state
    if "tool" in transcribed_text.lower() or "create" in transcribed_text.lower():
        SwarmState.swarm_actor_state = "coding"
    else:
        SwarmState.swarm_actor_state = "orchestrating"
        
    # Get current screen history state
    visual_context = visual_buffer.get_context_summary()
    
    # Get brain response
    response_text = await agent.chat(transcribed_text, visual_context=visual_context)
    
    SwarmState.swarm_actor_state = "standby"
    SwarmState.audio_status = "speaking"
    
    # Speak response
    await speaker.speak(response_text)
    
    SwarmState.audio_status = "standby"

async def main():
    global main_loop, wake_event, keyboard_triggered
    main_loop = asyncio.get_running_loop()
    wake_event = asyncio.Event()

    print("=" * 60)
    print("            JARVIS SWARM ASSISTANT SYSTEM (v3.0)            ")
    print("=" * 60)
    
    # 1. Initialize subsystems
    speaker = JarvisSpeaker()
    listener = JarvisListener()
    visual_buffer = JarvisVisualBuffer()
    agent = JarvisAgent()

    # Bind references to Web API shared state
    SwarmState.agent_ref = agent
    SwarmState.visual_buffer_ref = visual_buffer
    SwarmState.audio_status = "standby"
    SwarmState.swarm_actor_state = "standby"

    # 2. Start local FastAPI Web Server (HUD Dashboard) via Uvicorn in the same async loop if enabled
    server = None
    web_server_task = None
    if getattr(config, "ENABLE_WEB_SERVER", True):
        uvicorn_config = uvicorn.Config(
            "brain.web_server:app",
            host="127.0.0.1",
            port=8000,
            log_level="warning",
            loop="asyncio"
        )
        server = uvicorn.Server(uvicorn_config)
        web_server_task = asyncio.create_task(server.serve())
        print("[Main System] Holographic HUD Dashboard serving at: http://127.0.0.1:8000")

    # 3. Start ambient screen monitoring loop in background
    visual_task = asyncio.create_task(visual_buffer.run_loop())

    # 4. Register keyboard hotkey
    setup_keyboard_hotkey()

    # Determine if microphone is available
    has_mic = (listener.microphone is not None) or listener.has_sounddevice
    
    if not has_mic:
        print("\n[Main System] Microphone is not available. Running in CONSOLE MODE.")
        # Simulates startup greet
        SwarmState.audio_status = "speaking"
        await speaker.speak("Systems initialized. Running in console mode, sir. Dynamic HUD is live.")
        SwarmState.audio_status = "standby"
        
        # Console loop
        while True:
            try:
                user_input = await asyncio.to_thread(input, "\nType command (or 'exit' to quit) > ")
                if user_input.strip().lower() in ["exit", "quit", "shutdown"]:
                    SwarmState.audio_status = "speaking"
                    await speaker.speak("Shutting down systems. Goodbye, sir.")
                    break
                if user_input.strip():
                    await process_user_command(agent, speaker, listener, visual_buffer, user_input)
            except (KeyboardInterrupt, EOFError):
                break
        
        # Cleanup
        visual_buffer.stop()
        visual_task.cancel()
        if server:
            server.should_exit = True
        if web_server_task:
            web_server_task.cancel()
        return

    # Microphone is available, say hello
    SwarmState.audio_status = "speaking"
    await speaker.speak("Online and operational, sir. Synthetic nervous system is active.")
    SwarmState.audio_status = "standby"

    # 5. Main Listening Loop
    print("\n[JARVIS] Standing by. Say 'Jarvis' or press hotkey to wake.")
    
    while True:
        try:
            # Check if keyboard hotkey was pressed
            if keyboard_triggered:
                keyboard_triggered = False
                wake_event.clear()
                
                SwarmState.audio_status = "speaking"
                await speaker.speak("Listening, sir.")
                await asyncio.sleep(0.5)  # Small delay so mic doesn't pick up JARVIS's own voice
                
                SwarmState.audio_status = "listening"
                command = await asyncio.to_thread(listener.listen_and_transcribe)
                if command:
                    await process_user_command(agent, speaker, listener, visual_buffer, command)
                print("\n[JARVIS] Standing by...")
                
            # Check for audio wake word
            elif config.TRIGGER_MODE in ["voice", "hybrid"]:
                # Short checking periods
                is_woken = await asyncio.to_thread(listener.check_for_wake_word)
                if is_woken:
                    SwarmState.audio_status = "speaking"
                    await speaker.speak("Yes, sir?")
                    
                    SwarmState.audio_status = "listening"
                    command = await asyncio.to_thread(listener.listen_and_transcribe)
                    await process_user_command(agent, speaker, listener, visual_buffer, command)
                    print("\n[JARVIS] Standing by...")
                
            await asyncio.sleep(0.1)
            
        except KeyboardInterrupt:
            SwarmState.audio_status = "speaking"
            await speaker.speak("Powering down systems, sir. Have a pleasant day.")
            break
        except Exception as e:
            print(f"[Main Loop Error] Exception encountered: {e}")
            await asyncio.sleep(1)

    # Cleanup background tasks
    visual_buffer.stop()
    visual_task.cancel()
    if server:
        server.should_exit = True
    if web_server_task:
        web_server_task.cancel()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
