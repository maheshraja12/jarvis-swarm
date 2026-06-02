import subprocess
import os
import time
import sys
import psutil
import pyautogui
import webbrowser

# Add parent directory to path to allow importing config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def run_application(app_name: str, args: str = None) -> str:
    """Launches a local application on Windows, or opens a URL in browser."""
    app_name = app_name.strip().lower()
    
    # Check if args represents a URL and browser is requested
    if app_name in ["chrome", "browser", "firefox", "edge", "safari"] or (args and args.startswith(("http://", "https://", "www."))):
        url = args if args else "https://www.google.com"
        if url.startswith("www."):
            url = "https://" + url
        try:
            webbrowser.open(url)
            return f"Successfully opened browser to {url}, sir."
        except Exception as e:
            return f"Failed to open browser: {e}"

    # Map friendly app names to system executable commands
    app_map = {
        "notepad": "notepad.exe",
        "calc": "calc.exe",
        "calculator": "calc.exe",
        "explorer": "explorer.exe",
        "paint": "mspaint.exe",
        "mspaint": "mspaint.exe",
        "cmd": "cmd.exe",
        "terminal": "wt.exe" # Windows Terminal
    }
    
    cmd = app_map.get(app_name, app_name)
    
    try:
        if args:
            subprocess.Popen([cmd, args], shell=True)
        else:
            subprocess.Popen(cmd, shell=True)
        return f"Successfully launched {app_name}, sir."
    except Exception as e:
        # Try running directly as a shell execution fallback
        try:
            subprocess.Popen(cmd, shell=True)
            return f"Successfully launched {app_name} via shell command."
        except Exception as shell_err:
            return f"Failed to launch {app_name}. Error: {e} (Fallback: {shell_err})"

def get_system_stats() -> str:
    """Gets CPU usage, RAM utilization, and battery status."""
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        
        status = f"System performance report, sir:\n- CPU utilization is currently at {cpu}%\n- Memory usage is at {ram}%"
        
        if battery:
            plugged = "plugged in" if battery.power_plugged else "discharging"
            status += f"\n- Battery charge is at {battery.percent}% and {plugged}."
        else:
            status += "\n- Power stats: No battery detected (desktop system)."
            
        return status
    except Exception as e:
        return f"Error retrieving system stats: {e}"

def adjust_system_volume(action: str, percent: int = 10) -> str:
    """Adjusts volume using pyautogui media keys."""
    action = action.lower().strip()
    try:
        if action == "mute":
            pyautogui.press("volumemute")
            return "Audio muted, sir."
        elif action == "unmute":
            pyautogui.press("volumemute")
            return "Audio unmuted, sir."
        
        # Volume adjustments
        # PyAutoGUI 'volumeup' / 'volumedown' adjusts by 2% increments on Windows
        press_count = max(1, round(percent / 2))
        
        if action == "up":
            for _ in range(press_count):
                pyautogui.press("volumeup")
            return f"Volume increased by {percent}%, sir."
        elif action == "down":
            for _ in range(press_count):
                pyautogui.press("volumedown")
            return f"Volume decreased by {percent}%, sir."
        else:
            return f"Unknown volume action '{action}', sir."
    except Exception as e:
        return f"Failed to adjust volume: {e}"

def take_screenshot() -> str:
    """Takes a full screen screenshot and saves it to config.SCREENSHOT_DIR."""
    try:
        filename = f"screenshot_{int(time.time())}.png"
        filepath = os.path.join(config.SCREENSHOT_DIR, filename)
        
        # Take screenshot using pyautogui
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        
        # Normalize path for print
        clean_path = filepath.replace("\\", "/")
        return f"Screenshot successfully captured and saved as {filename}, sir."
    except Exception as e:
        return f"Could not take screenshot. Error: {e}"

# Simple self-test if run directly
if __name__ == "__main__":
    print(get_system_stats())
    print("Testing calculator launch...")
    print(run_application("calculator"))
    time.sleep(1)
    print("Testing screenshot...")
    print(take_screenshot())
