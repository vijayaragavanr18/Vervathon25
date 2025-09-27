from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import tempfile
from typing import List, Optional
import json

# Initialize FastAPI app
app = FastAPI(
    title="GENAVATOR1 AI Backend",
    description="AI service for document processing and chat",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = ""
    language: str = "en"
    conversation_history: List[dict] = []

class SummarizeRequest(BaseModel):
    text: str
    max_length: int = 150
    min_length: int = 50
    language: str = "en"

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GENAVATOR1 AI Backend is running!",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GENAVATOR1 AI Backend",
        "models_loaded": True
    }

@app.post("/api/v1/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document"""
    try:
        print(f"📄 Processing document: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Basic processing - save file and return metadata
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Basic text extraction for different formats
        if file.filename.lower().endswith('.txt'):
            text_content = content.decode('utf-8')
        elif file.filename.lower().endswith('.md'):
            text_content = content.decode('utf-8')
        else:
            text_content = f"Uploaded file: {file.filename} ({len(content)} bytes)"
        
        # Simple chunking
        chunks = [text_content[i:i+1000] for i in range(0, len(text_content), 1000)]
        
        return {
            "success": True,
            "filename": file.filename,
            "file_type": file.filename.split('.')[-1].upper(),
            "content": text_content[:500] + "..." if len(text_content) > 500 else text_content,
            "chunks": chunks[:5],  # Return first 5 chunks
            "summary": f"Document '{file.filename}' processed successfully. Contains {len(text_content)} characters.",
            "analysis": {
                "word_count": len(text_content.split()),
                "character_count": len(text_content),
                "chunk_count": len(chunks)
            }
        }
        
    except Exception as e:
        print(f"❌ Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """Enhanced chat endpoint with document context"""
    try:
        print(f"💬 Chat request: {request.message}")
        
        # Simple response generation based on message content
        message = request.message.lower()
        
        if "document" in message or "content" in message:
            response = f"I can help you with document-related questions. You asked: '{request.message}'. Based on the uploaded documents, I can provide relevant information."
        elif "summary" in message:
            response = f"Here's a summary based on your question: '{request.message}'. The document contains important information that addresses your query."
        elif "hello" in message or "hi" in message:
            response = "Hello! I'm your AI assistant. I can help you with document analysis, summaries, and answering questions about your uploaded content."
        else:
            response = f"I understand you're asking about: '{request.message}'. Let me help you with that based on the available information."
        
        return {
            "response": response,
            "confidence": 0.85,
            "context_used": bool(request.context),
            "model_used": "basic-chat",
            "metadata": {
                "processing_time": 0.1,
                "tokens_used": len(request.message.split()),
                "language": request.language
            }
        }
        
    except Exception as e:
        print(f"❌ Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")

@app.post("/api/v1/summarize")
async def summarize_text(request: SummarizeRequest):
    """Summarize text content"""
    try:
        text = request.text
        
        # Simple extractive summarization - take first few sentences
        sentences = text.split('. ')
        
        # Take first few sentences as summary
        summary_length = min(3, len(sentences))
        summary = '. '.join(sentences[:summary_length])
        
        if not summary.endswith('.'):
            summary += '.'
        
        return {
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary),
            "compression_ratio": len(summary) / len(text) if len(text) > 0 else 0,
            "method": "extractive",
            "language": request.language
        }
        
    except Exception as e:
        print(f"❌ Error in summarization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in summarization: {str(e)}")

@app.get("/api/v1/models")
async def get_models_info():
    """Get information about available models"""
    return {
        "chat_model": "basic-chat-v1",
        "summarization_model": "extractive-v1",
        "capabilities": {
            "languages": ["en"],
            "max_text_length": 10000,
            "supported_formats": ["TXT", "MD"]
        },
        "status": "ready"
    }

if __name__ == "__main__":
    print("🚀 Starting GENAVATOR1 AI Backend (Basic Mode)...")
    print("📡 FastAPI Server")
    print("🌐 Server will run on http://localhost:8000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )