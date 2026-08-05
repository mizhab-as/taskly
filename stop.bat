@echo off
REM Taskly — Windows stop script

cd /d "%~dp0"

echo Stopping Taskly processes...
taskkill /FI "WINDOWTITLE eq server.py*" /F 2>nul
taskkill /FI "WINDOWTITLE eq reminders.py*" /F 2>nul

echo Done.
