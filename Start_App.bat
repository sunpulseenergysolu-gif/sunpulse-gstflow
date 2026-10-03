@echo off
title SunPulse GSTFlow Invoicing App
color 0b
cd /d "%~dp0"

echo ================================================================
echo           SUNPULSE GSTFLOW - INVOICING & STORAGE SUITE
echo ================================================================
echo.
echo [1/2] Opening application in your default browser...
start http://127.0.0.1:8000

echo [2/2] Starting local GSTFlow server...
python -m uvicorn main:app --host 0.0.0.0 --port 8000

pause
