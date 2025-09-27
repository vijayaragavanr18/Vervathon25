#!/bin/bash

# GENAVATOR1 Setup Script
# This script sets up the complete GENAVATOR1 system

echo "🚀 Setting up GENAVATOR1 AI Educational Avatar..."
echo ""

# Check Python installation
echo "📋 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi
echo "✅ Python found: $(python3 --version)"

# Check Node.js installation
echo "📋 Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 14+ first."
    exit 1
fi
echo "✅ Node.js found: $(node --version)"

# Set up AI Backend
echo ""
echo "🧠 Setting up AI Backend..."
cd ai-backend
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi
echo "✅ Python dependencies installed"
cd ..

# Set up Node.js Backend
echo ""
echo "🗄️  Setting up Node.js Backend..."
cd backend
echo "📦 Installing Node.js dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi
echo "✅ Node.js dependencies installed"
cd ..

echo ""
echo "🎉 GENAVATOR1 setup complete!"
echo ""
echo "🚀 To start the system:"
echo "1. Start AI Backend:    cd ai-backend && python genavator_main.py"
echo "2. Start Node.js:       cd backend && node server.js"
echo "3. Start Frontend:      python -m http.server 3000"
echo "4. Open browser:        http://localhost:3000/ai-educational-avatar.html"
echo ""
echo "💡 Or use the start_all_servers script for convenience!"
echo ""