@echo off
echo =======================================================
echo    MOVIE RECOMMENDATION SYSTEM - LOCAL DEPLOYMENT
echo =======================================================
echo.

cd /d "%~dp0"

echo 🚀 Starting Movie Recommendation System...
echo.

echo 📦 Activating virtual environment...
call "..\..\.venv\Scripts\activate.bat"

echo ⚡ Starting FastAPI Backend...
start "Backend Server" cmd /k python api.py

echo ⏳ Waiting 10 seconds for backend to initialize...
timeout /t 10 /nobreak > nul

echo 🌐 Starting Frontend Server...
start "Frontend Server" cmd /k "cd frontend && python -m http.server 8080 --bind 127.0.0.1"

echo ⏳ Waiting 3 seconds for frontend to start...
timeout /t 3 /nobreak > nul

echo 🌍 Opening application in browser...
start http://localhost:8080

echo.
echo =======================================================
echo ✅ MOVIE RECOMMENDATION SYSTEM IS NOW RUNNING!
echo =======================================================
echo 🔗 Frontend:     http://localhost:8080
echo 🔗 Backend API:  http://localhost:8000  
echo 📚 API Docs:     http://localhost:8000/docs
echo 📊 Health Check: http://localhost:8000/health
echo 📈 Metrics:      http://localhost:8000/metrics
echo.
echo 💡 Features Available:
echo    • Netflix-style movie browsing interface
echo    • Real-time movie recommendations  
echo    • Performance metrics dashboard
echo    • Fuzzy logic + Neural network hybrid system
echo    • Advanced collaborative filtering
echo    • User clustering and personalization
echo    • Intelligent recommendation explanations
echo.
echo ⌨️  Close the terminal windows to stop the servers
echo =======================================================
echo.
pause