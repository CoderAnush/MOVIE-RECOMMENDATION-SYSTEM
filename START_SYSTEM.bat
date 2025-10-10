@echo off
REM ================================================================
REM Complete Movie Recommendation System - Startup Script
REM ================================================================
REM This script starts the backend API and frontend server
REM ================================================================

echo.
echo ================================================================
echo  MOVIE RECOMMENDATION SYSTEM - Full 10M Dataset
echo ================================================================
echo.
echo Starting backend API server on http://127.0.0.1:3000...
echo.

cd /d "%~dp0"

REM Start backend in a new window
start "Backend API - Port 3000" cmd /k "python -m uvicorn api:app --host 127.0.0.1 --port 3000"

REM Wait for backend to load
echo Waiting 30 seconds for backend to load 10M dataset...
timeout /t 30 /nobreak

REM Open browser
echo.
echo Opening browser...
start http://127.0.0.1:3000

echo.
echo ================================================================
echo  SYSTEM RUNNING!
echo ================================================================
echo  Backend API + Frontend:  http://127.0.0.1:3000
echo  API Docs:     http://127.0.0.1:3000/docs
echo  Health Check: http://127.0.0.1:3000/health
echo ================================================================
echo.
echo Close the backend and frontend windows to stop the system.
echo.
pause
