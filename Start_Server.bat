@echo off
echo Starting FastAPI Server for CHF Members System...
echo Please leave this black window open while using the system.
echo.
cd /d "C:\Users\USER\Desktop\CHF JOINED DATA\backend"
py -m uvicorn main:app --reload
pause
