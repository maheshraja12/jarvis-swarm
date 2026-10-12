@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher not found. Install Python 3.11 or newer and enable PATH.
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -3.11 -m venv .venv
if errorlevel 1 exit /b 1
if not exist ".env" copy ".env.example" ".env" >nul
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" main.py
endlocal
