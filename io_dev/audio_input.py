import asyncio
import os
import sys
import tempfile
import numpy as np
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr

# Add parent directory to path to allow importing config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

class JarvisListener:
    """Manages audio recording, wake word detection, and speech-to-text transcription."""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = config.STT_ENERGY_THRESHOLD
        self.recognizer.dynamic_energy_threshold = True
        self.microphone = None
        self.has_sounddevice = True
        self.temp_wav = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_input.wav")
        self._init_audio()

    def _init_audio(self):
        """Attempts to initialize standard microphone or checks for sounddevice availability."""
        self.sd_energy_threshold = 80.0
        try:
            # Try PyAudio-dependent sr.Microphone first
            self.microphone = sr.Microphone()
            # Calibrate
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("[Listener System] Standard PyAudio microphone initialized.")
        except Exception as e:
            print(f"[Listener Warning] Standard PyAudio mic init failed: {e}")
            self.microphone = None
            
            # Verify sounddevice fallback works
            try:
                devices = sd.query_devices()
                # Check if there is an input device
                input_devs = [d for d in devices if d.get('max_input_channels', 0) > 0]
                if input_devs:
                    self.has_sounddevice = True
                    default_dev = sd.query_devices(kind='input')
                    print(f"[Listener System] PyAudio missing. Activated sounddevice input fallback (Device: {default_dev['name']}).")
                    
                    # Calibrate dynamic energy threshold for sounddevice
                    print("[Listener System] Calibrating microphone noise floor...")
                    sample_rate = 16000
                    calib_data = sd.rec(int(0.4 * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
                    sd.wait()
                    ambient_rms = np.sqrt(np.mean(calib_data**2)) if len(calib_data) > 0 else 50.0
                    self.sd_energy_threshold = max(ambient_rms * 1.6, 60.0)
                    print(f"[Listener System] Mic calibrated. Ambient RMS: {ambient_rms:.2f}, threshold set to {self.sd_energy_threshold:.2f}")
                else:
                    self.has_sounddevice = False
                    print("[Listener Warning] No input audio devices detected by sounddevice.")
            except Exception as sd_err:
                self.has_sounddevice = False
                print(f"[Listener Warning] sounddevice fallback check failed: {sd_err}")

    def listen_and_transcribe(self, timeout=None) -> str:
        """Listens to the microphone and returns the transcribed text. Uses sounddevice if PyAudio is missing."""
        timeout = timeout or config.STT_RECORD_TIMEOUT
        
        if self.microphone:
            # Standard PyAudio listening path
            try:
                with self.microphone as source:
                    print("\n[Listening...]")
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)
                print("[Processing speech...]")
                text = self.recognizer.recognize_google(audio)
                print(f"[You]: {text}")
                return text.strip()
            except Exception as e:
                print(f"[Listener Debug] PyAudio listen failed: {e}")
                return ""
        elif self.has_sounddevice:
            # High-resilience sounddevice fallback path
            try:
                print(f"\n[Listening via sounddevice (max {timeout}s)...]")
                sample_rate = 16000
                
                # Record chunk with energy threshold tracking to stop on silence
                chunk_duration = 0.4
                chunk_samples = int(chunk_duration * sample_rate)
                recorded_chunks = []
                
                silence_limit = 1.6  # Seconds of silence before stopping
                silence_chunks_limit = int(silence_limit / chunk_duration)
                silence_counter = 0
                started_speaking = False
                
                max_chunks = int(timeout / chunk_duration)
                
                # Record stream block using sounddevice InputStream continuously
                with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
                    for _ in range(max_chunks):
                        # Read a short chunk
                        chunk, overflowed = stream.read(chunk_samples)
                        
                        # Compute energy of the chunk
                        energy = np.sqrt(np.mean(chunk**2)) if len(chunk) > 0 else 0
                        
                        # Threshold detection
                        if energy > self.sd_energy_threshold:  # Speak detected threshold
                            started_speaking = True
                            silence_counter = 0
                        elif started_speaking:
                            silence_counter += 1
                            
                        recorded_chunks.append(chunk)
                        
                        # Stop if user stopped speaking
                        if started_speaking and silence_counter >= silence_chunks_limit:
                            break
                
                if not recorded_chunks:
                    return ""
                    
                full_recording = np.concatenate(recorded_chunks, axis=0)
                
                # Use speech_recognition AudioData directly from raw memory bytes
                print("[Processing speech...]")
                audio_data = sr.AudioData(full_recording.tobytes(), sample_rate, 2)
                
                text = self.recognizer.recognize_google(audio_data)
                print(f"[You]: {text}")
                
                return text.strip()
            except Exception as e:
                print(f"[Listener Debug] sounddevice listen failed: {e}")
                return ""
        else:
            print("[Listener Error] No input audio devices or drivers available.")
            return ""

    def check_for_wake_word(self) -> bool:
        """Listens to a very brief audio snippet to check if the wake word was spoken."""
        if self.microphone:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=2.0, phrase_time_limit=2.5)
                text = self.recognizer.recognize_google(audio).lower().strip()
                for wake_word in config.WAKE_WORDS:
                    if wake_word in text:
                        print(f"\n[Wake Word Detected]: Found '{wake_word}' in '{text}'")
                        return True
                return False
            except Exception:
                return False
        elif self.has_sounddevice:
            # sounddevice wake word check
            try:
                sample_rate = 16000
                duration = 2.2
                # Fast record
                recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
                sd.wait()
                
                # Use speech_recognition AudioData directly from memory bytes
                audio_data = sr.AudioData(recording.tobytes(), sample_rate, 2)
                text = self.recognizer.recognize_google(audio_data).lower().strip()
                
                for wake_word in config.WAKE_WORDS:
                    if wake_word in text:
                        print(f"\n[Wake Word Detected]: Found '{wake_word}' in '{text}'")
                        return True
                return False
            except Exception:
                return False
        return False
