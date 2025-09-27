@echo off
REM GENAVATOR1 Setup Script for Windows
REM This script sets up the complete GENAVATOR1 system

echo 🚀 Setting up GENAVATOR1 AI Educational Avatar...
echo.

REM Check Python installation
echo 📋 Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)
python --version
echo ✅ Python found

REM Check Node.js installation
echo 📋 Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 14+ first.
    pause
    exit /b 1
)
node --version
echo ✅ Node.js found

REM Set up AI Backend
echo.
echo 🧠 Setting up AI Backend...
cd ai-backend
echo 📦 Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)
echo ✅ Python dependencies installed
cd ..

REM Set up Node.js Backend
echo.
echo 🗄️ Setting up Node.js Backend...
cd backend
echo 📦 Installing Node.js dependencies...
npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install Node.js dependencies
    pause
    exit /b 1
)
echo ✅ Node.js dependencies installed
cd ..

echo.
echo 🎉 GENAVATOR1 setup complete!
echo.
echo 🚀 To start the system:
echo 1. Start AI Backend:    cd ai-backend ^&^& python genavator_main.py
echo 2. Start Node.js:       cd backend ^&^& node server.js
echo 3. Start Frontend:      python -m http.server 3000
echo 4. Open browser:        http://localhost:3000/ai-educational-avatar.html
echo.
echo 💡 Or use the START_ALL_SERVERS.bat script for convenience!
echo.
pause