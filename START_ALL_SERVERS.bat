@echo off
echo ========================================
echo    Starting AI Educational Avatar
echo ========================================
echo.

echo [1/3] Starting Node.js Backend (Port 3001)...
cd /d "C:\Users\vijay\OneDrive\Desktop\Vervevina\Genavator1\GenAvator1\backend"
start "Node.js Backend" cmd /k "node server.js"

timeout /t 3 /nobreak >nul

echo [2/3] Starting FastAPI AI Backend (Port 8000)...
cd /d "C:\Users\vijay\OneDrive\Desktop\Vervevina\Genavator1\GenAvator1\ai-backend"
start "FastAPI Backend" cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [3/3] Starting Frontend Server (Port 3000)...
cd /d "C:\Users\vijay\OneDrive\Desktop\Vervevina\Genavator1\GenAvator1"
start "Frontend Server" cmd /k "python -m http.server 3000"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo ✅ ALL SERVERS STARTED!
echo ========================================
echo.
echo 🌍 Frontend:     http://localhost:3000/ai-educational-avatar.html
echo 🚀 Node.js API:  http://localhost:3001/api/health
echo 🤖 FastAPI:      http://localhost:8000/docs
echo.
echo Press any key to continue...
pause >nul