@echo off
REM ─────────────────────────────────────────────────────────────
REM  Taskly — Windows Launcher
REM  Starts Flask API server + reminders daemon, opens browser.
REM ─────────────────────────────────────────────────────────────

SET PORT=5050
SET SCRIPT_DIR=%~dp0

echo.
echo   Taskly Launcher
echo   ===============
echo.

REM Kill any existing server on port 5050
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%PORT%"') do (
    taskkill /f /pid %%a >nul 2>&1
)

REM Install dependencies
echo   [1/3] Installing Python dependencies...
pip install -r requirements.txt -q

REM Start Flask server in background
echo   [2/3] Starting Python API server (localhost:%PORT%)...
start /b "" python server.py > data\server.log 2>&1

REM Wait for server to start
timeout /t 2 /nobreak >nul

REM Start reminders daemon in background
echo   [3/3] Starting reminder daemon...
start /b "" python reminders.py > data\reminders.log 2>&1

REM Open browser
echo   Opening Taskly at http://localhost:%PORT%
start http://localhost:%PORT%

echo.
echo   Taskly is running!
echo   Web app  - http://localhost:%PORT%
echo   API      - http://localhost:%PORT%/api/health
echo   Export   - python export.py
echo   Stop     - Close this window or run stop.bat
echo.
