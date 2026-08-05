@echo off
REM ─────────────────────────────────────────────────────────────
REM  Taskly — Windows Launcher
REM  Starts Python API server + reminder daemon, then opens app
REM ─────────────────────────────────────────────────────────────

cd /d "%~dp0"

echo.
echo   ┌─────────────────────────────────────────────┐
echo   │              Taskly Launcher                 │
echo   └─────────────────────────────────────────────┘
echo.

echo   -- Installing Python dependencies...
python -m pip install -r requirements.txt -q 2>nul

echo   -- Starting Taskly Python Server (http://localhost:5050)...
start /b python server.py > data\server.log 2>&1

echo   -- Starting Reminder Daemon...
start /b python reminders.py > data\reminders.log 2>&1

timeout /t 2 /nobreak >nul

echo   -- Opening Taskly in your default browser...
start http://localhost:5050

echo.
echo   Taskly is running!
echo   Web app  : http://localhost:5050
echo   API      : http://localhost:5050/api/health
echo   Export   : python export.py
echo.
