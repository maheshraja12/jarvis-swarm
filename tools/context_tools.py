import pygetwindow as gw
import pyperclip
import os
import sys

# Win32gui is highly reliable on Windows, imported if available
try:
    import win32gui
    import win32process
    import psutil
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

def get_screen_context() -> str:
    """Returns the title and process of the currently active/foreground window."""
    try:
        if HAS_WIN32:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            
            # Retrieve process info to give more detailed context (e.g. Chrome, Acrobat Reader)
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc = psutil.Process(pid)
                proc_name = proc.name()
            except Exception:
                proc_name = "Unknown Process"
                
            if title:
                return f"Active window: '{title}' (Process: {proc_name}), sir."
            else:
                return f"The active application is '{proc_name}', but it has no window title."
        else:
            # Fallback to pygetwindow
            active_window = gw.getActiveWindow()
            if active_window and active_window.title:
                return f"Active window: '{active_window.title}', sir."
            else:
                return "I couldn't detect the active window name, sir."
    except Exception as e:
        return f"Error retrieving screen context: {e}"

def get_clipboard_text() -> str:
    """Gets the current text content from the clipboard."""
    try:
        content = pyperclip.paste()
        if content and content.strip():
            # Truncate clipboard content if it is too long to prevent LLM context overflow
            content_str = content.strip()
            if len(content_str) > 1500:
                content_str = content_str[:1500] + "\n... [truncated due to length]"
            return f"Clipboard Content:\n\"\"\"\n{content_str}\n\"\"\""
        else:
            return "The clipboard is currently empty, sir."
    except Exception as e:
        return f"Failed to retrieve clipboard content: {e}"

# Simple self-test if run directly
if __name__ == "__main__":
    print(get_screen_context())
    print(get_clipboard_text())
