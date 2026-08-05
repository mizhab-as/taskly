@echo off
REM Taskly — Windows Stop Script

echo   Stopping Taskly...

REM Kill server on port 5050
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5050"') do (
    taskkill /f /pid %%a >nul 2>&1
)

REM Kill reminders daemon by name
taskkill /f /im python.exe /fi "WINDOWTITLE eq reminders*" >nul 2>&1

del /f /q data\server.pid data\reminders.pid 2>nul

echo   Done.
