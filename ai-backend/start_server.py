#!/usr/bin/env python3
"""
Simple FastAPI server starter - no reload mode to avoid issues
"""
import uvicorn
from main import app

if __name__ == "__main__":
    print("🚀 Starting GENAVATOR1 AI Backend...")
    print("📡 FastAPI + Hugging Face Integration")
    print("🌐 Server will run on http://localhost:8000")
    
    # Start without reload to avoid interruption issues
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to prevent interruption
        log_level="info"
    )