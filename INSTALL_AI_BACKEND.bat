@echo off
echo ========================================
echo   Installing Enhanced AI Backend
echo ========================================
echo.

cd /d "C:\Users\vijay\OneDrive\Desktop\Vervevina\Genavator1\GenAvator1\ai-backend"

echo [1/5] Installing Core FastAPI packages...
python -m pip install fastapi uvicorn python-multipart aiofiles --quiet

echo [2/5] Installing Enhanced Document Processing (PyMuPDF)...
python -m pip install PyMuPDF sentence-transformers --quiet

echo [3/5] Installing Hugging Face Transformers...
python -m pip install transformers torch tokenizers --quiet

echo [4/5] Installing Additional Document Support...
python -m pip install python-docx openpyxl pandas numpy --quiet

echo [5/5] Installing NLP Tools...
python -m pip install nltk beautifulsoup4 requests pydantic --quiet

echo.
echo [6/6] Downloading NLTK data...
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); print('✅ NLTK data downloaded')"

echo.
echo ========================================
echo ✅ ENHANCED AI BACKEND READY!
echo ========================================
echo.
echo 🎯 Features Available:
echo   • PyMuPDF PDF processing
echo   • Document-aware chat (RAG)  
echo   • Semantic chunking
echo   • Multiple AI models
echo   • Advanced summarization
echo.
echo Now you can run START_ALL_SERVERS.bat
echo.
pause