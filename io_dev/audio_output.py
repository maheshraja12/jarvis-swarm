import asyncio
import os
import sys
import subprocess
import pyttsx3

# Add parent directory to path to allow importing config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

class JarvisSpeaker:
    """Handles speech synthesis using pyttsx3 (local/offline) or edge-tts (online/natural)."""
    
    def __init__(self):
        # Initialize pyttsx3 engine as a local offline fallback
        try:
            self.pyttsx_engine = pyttsx3.init()
            # Try setting to a male/female system voice
            voices = self.pyttsx_engine.getProperty("voices")
            if voices:
                # Typically index 0 is Microsoft David (male) and index 1 is Zira (female)
                self.pyttsx_engine.setProperty("voice", voices[0].id)
            self.pyttsx_engine.setProperty("rate", config.PYTTSX3_RATE)
        except Exception as e:
            print(f"[Speaker Init Error] Pyttsx3 offline synthesizer failed: {e}")
            self.pyttsx_engine = None

    async def speak(self, text: str):
        """Speaks the text using the configured TTS engine, with automatic fallback."""
        text = text.strip()
        if not text:
            return

        # Print the text so it's visible in console
        print(f"[JARVIS Response]: {text}")
        
        # Strip markdown symbols for speech synthesis (so JARVIS doesn't say "star star" or "bracket link")
        clean_text = self._clean_for_speech(text)

        if config.DEFAULT_TTS_ENGINE == "edge-tts":
            # Attempt to use Edge TTS
            success = await self._speak_edge(clean_text)
            if not success:
                # Automatically fall back to local offline TTS if edge-tts failed (e.g. no internet)
                print("[Speaker System] Edge-TTS failed or is offline. Falling back to offline synthesizer...")
                self._speak_pyttsx(clean_text)
        else:
            self._speak_pyttsx(clean_text)

    async def _speak_edge(self, text: str) -> bool:
        """Helper to generate and play speech using Microsoft Edge TTS."""
        import tempfile
        import time
        temp_file = os.path.join(tempfile.gettempdir(), f"jarvis_speech_{int(time.time()*1000)}.mp3")
        try:
            # Import edge_tts dynamically to handle import errors
            import edge_tts
            
            communicate = edge_tts.Communicate(text, config.EDGE_TTS_VOICE)
            await communicate.save(temp_file)
            
            # Check if file was created and is non-empty
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                # Play using native Windows COM WMPlayer.OCX via a background thread
                await asyncio.to_thread(self._play_mp3_windows, temp_file)
                
                # Try to delete temporary file after speaking
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
                return True
        except Exception as e:
            print(f"[Speaker Warning] Edge TTS execution failed: {e}")
            
        # Clean up if file exists
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
        return False

    def _speak_pyttsx(self, text: str):
        """Helper to speak using offline pyttsx3 engine."""
        if not self.pyttsx_engine:
            print(f"[Speaker Error] Offline synthesizer is unavailable. Spoken output: {text}")
            return
            
        try:
            self.pyttsx_engine.say(text)
            self.pyttsx_engine.runAndWait()
        except Exception as e:
            print(f"[Speaker Error] Pyttsx3 speak failed: {e}")

    def _play_mp3_windows(self, file_path: str):
        """Plays an MP3 file using built-in Windows Media Player COM object via PowerShell."""
        # Convert path to absolute backslash formatting for Windows
        abs_path = os.path.abspath(file_path).replace("/", "\\")
        
        # PowerShell script creates a hidden Windows Media Player object, plays the file,
        # and loops with a safety timeout (default 10s or dynamic duration + 2s) to prevent hanging.
        ps_cmd = (
            f"$player = New-Object -ComObject WMPlayer.OCX; "
            f"$player.URL = '{abs_path}'; "
            f"$player.controls.play(); "
            f"$start = Get-Date; "
            f"$playing = $false; "
            f"$timeout = 10; "
            f"while (((Get-Date) - $start).TotalSeconds -lt $timeout) {{ "
            f"  $state = $player.playState; "
            f"  if ($state -eq 3) {{ "
            f"    $playing = $true; "
            f"    $duration = $player.currentMedia.duration; "
            f"    if ($duration -gt 0) {{ $timeout = $duration + 2 }} "
            f"  }} "
            f"  if ($playing -and ($state -eq 1 -or $state -eq 8)) {{ break }} "
            f"  Start-Sleep -Milliseconds 100 "
            f"}}; "
            f"$player.close(); "
            f"[System.Runtime.Interopservices.Marshal]::ReleaseComObject($player) | Out-Null"
        )
        
        subprocess.run(
            ["powershell", "-Command", ps_cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW # Run silently without popping console windows
        )

    def _clean_for_speech(self, text: str) -> str:
        """Cleans formatting, links, and code blocks from text to make it suitable for speech."""
        import re
        # Remove Markdown bold/italic
        text = text.replace("**", "").replace("*", "").replace("`", "")
        # Remove markdown URLs: [text](link) -> text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Remove lines starting with markdown headers
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        # Replace list dashes with small spaces
        text = re.sub(r'^-\s+', ' ', text, flags=re.MULTILINE)
        return text.strip()

# Simple self-test if run directly
if __name__ == "__main__":
    speaker = JarvisSpeaker()
    print("Testing speaking with Edge TTS voice...")
    asyncio.run(speaker.speak("Greetings, sir. I am JARVIS. Your systems are fully operational."))
    
    # Toggle to Pyttsx3 for testing
    config.DEFAULT_TTS_ENGINE = "pyttsx3"
    print("Testing speaking with Offline Pyttsx3...")
    asyncio.run(speaker.speak("This is the offline system voice fallback speaking."))
