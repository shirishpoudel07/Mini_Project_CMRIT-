@echo off
title XRayAI Streamlit Dashboard
echo ============================================================
echo   Starting XRayAI Streamlit Clinical Dashboard on :8501...
echo ============================================================
echo.
if exist ".\.venv\Scripts\python.exe" (
    .\.venv\Scripts\python.exe -m streamlit run app.py
) else (
    py -3.14 -m streamlit run app.py
)
pause
