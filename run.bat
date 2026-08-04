@echo off
REM Launcher script for Tudy To-Do List Application on Windows

cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% equ 0 (
    python main.py %*
    goto end
)

where python3 >nul 2>nul
if %errorlevel% equ 0 (
    python3 main.py %*
    goto end
)

echo Error: Python was not found in your PATH.
echo Please install Python 3.9 or higher.
pause

:end
