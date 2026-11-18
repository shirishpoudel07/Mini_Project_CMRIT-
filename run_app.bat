@echo off
title XRayAI Clinical Workstation & API Server
echo ============================================================
echo   Starting XRayAI Clinical React Workstation & Backend API...
echo ============================================================
echo.
if exist ".\.venv\Scripts\python.exe" (
    .\.venv\Scripts\python.exe api_server.py
) else (
    py -3.14 api_server.py
)
pause
