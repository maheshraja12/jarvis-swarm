import sounddevice as sd
import numpy as np
import speech_recognition as sr

def diagnose():
    print("=" * 60)
    print("         JARVIS MICROPHONE & STT DIAGNOSTIC")
    print("=" * 60)
    
    # 1. Query Devices
    try:
        devices = sd.query_devices()
        input_dev = sd.query_devices(kind='input')
        print(f"[Mic status] Default input device: '{input_dev['name']}'")
    except Exception as e:
        print(f"[ERROR] Could not query audio devices: {e}")
        return

    # 2. Record Test
    sample_rate = 16000
    duration = 4.0
    print(f"\n[Action] Recording {duration} seconds. Please say 'Hello Jarvis' clearly into your microphone now!")
    
    try:
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()
    except Exception as e:
        print(f"[ERROR] Microphone recording failed: {e}")
        return
        
    print("\n[Processing] Analyzing audio levels...")
    max_val = np.max(np.abs(recording))
    rms_val = np.sqrt(np.mean(recording**2))
    
    print(f"  - Peak amplitude: {max_val} (out of 32768)")
    print(f"  - RMS Energy level: {rms_val:.2f}")
    
    if rms_val < 10.0:
        print("[WARNING] The recording was extremely quiet or silent. Please check if your microphone is muted in Windows settings or if the input gain is too low.")
        return
        
    # 3. Transcribe Test
    print("\n[Action] Sending audio to Google Speech Recognition...")
    recognizer = sr.Recognizer()
    audio_data = sr.AudioData(recording.tobytes(), sample_rate, 2)
    
    try:
        text = recognizer.recognize_google(audio_data)
        print(f"\n[SUCCESS] Google transcribing result: '{text}'")
        print("\nYour microphone and internet-connected STT are working perfectly! You can run python main.py and talk.")
    except sr.UnknownValueError:
        print("\n[FAILED] Google Speech Recognition could not understand the audio. It was either too quiet or unclear.")
    except sr.RequestError as e:
        print(f"\n[ERROR] Could not request results from Google Speech Recognition service: {e}")
        print("Please check your internet connection.")

if __name__ == "__main__":
    diagnose()
