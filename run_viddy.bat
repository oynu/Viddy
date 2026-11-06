@echo off
title Viddy — Autonomous AI Video Studio
cd /d "%~dp0"

echo ========================================================
echo   Launching Viddy Autonomous AI Video Studio...
echo ========================================================

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run_viddy.py %*
) else (
    python run_viddy.py %*
)

pause
