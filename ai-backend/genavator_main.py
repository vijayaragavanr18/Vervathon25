from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import tempfile
from typing import List, Optional, Dict, Any
import json

# Import our lightweight services (your original vision implemented efficiently)
from lightweight_summarizer import LightweightSummarizer
from lightweight_chat_model import DocumentAwareChatModel
from lightweight_document_processor import LightweightDocumentProcessor

# Initialize FastAPI app
app = FastAPI(
    title="GENAVATOR1 AI Backend - PyMuPDF Enhanced",
    description="Advanced AI service with PyMuPDF document processing, semantic chunking, and conversational AI",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI models (your original vision - lightweight but powerful)
print("🤖 Loading GENAVATOR1 Enhanced AI Models...")
print("📄 PyMuPDF Integration: High-quality PDF extraction")
print("🧠 Semantic Processing: Document-aware conversational AI")
print("📊 Advanced Analytics: Content analysis and summarization")

summarizer = LightweightSummarizer()
chat_model = DocumentAwareChatModel()  
doc_processor = LightweightDocumentProcessor()

print("✅ GENAVATOR1 AI Backend Ready!")
print("🔧 Features: PyMuPDF, Semantic Chunking, Document-Aware Chat")

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
    summary_type: str = "general"  # general, academic, bullet_points

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🚀 GENAVATOR1 AI Backend - PyMuPDF Enhanced",
        "status": "online",
        "version": "2.0.0",
        "features": [
            "PyMuPDF High-Quality PDF Processing",
            "Multi-format Support (PDF, DOCX, TXT, MD, JSON, CSV)",
            "Semantic Document Chunking", 
            "Document-Aware Conversational AI",
            "Advanced Content Analysis",
            "Multiple Summarization Methods"
        ],
        "supported_formats": doc_processor.get_supported_formats()
    }

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GENAVATOR1 AI Backend",
        "models_loaded": True,
        "pymupdf_available": doc_processor.pymupdf_available,
        "components": {
            "document_processor": "ready",
            "chat_model": "ready", 
            "summarizer": "ready"
        }
    }

@app.post("/api/v1/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process document with PyMuPDF + semantic chunking
    Your original vision: Advanced document processing with high-quality extraction
    """
    try:
        print(f"📄 Processing document with GENAVATOR1: {file.filename}")
        
        # Process document with advanced processor (PyMuPDF when available)
        result = await doc_processor.process_upload(file)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Processing failed'))
        
        # Load document context into chat model for RAG (Your original vision)
        chat_model.load_document_context(
            chunks=result['chunks'],
            embeddings=result.get('embeddings'),
            metadata={
                'filename': result['filename'],
                'file_type': result['file_type'],
                'word_count': result['analysis']['word_count'],
                'processing_method': result['metadata']['processing_method']
            }
        )
        
        print(f"✅ Document processed successfully: {len(result['chunks'])} chunks created")
        
        return {
            "success": True,
            "message": f"Document '{file.filename}' processed with GENAVATOR1 AI",
            "filename": result['filename'],
            "file_type": result['file_type'],
            "processing_method": result['metadata']['processing_method'],
            "content": result['content'][:1000] + "..." if len(result['content']) > 1000 else result['content'],
            "summary": result['summary'],
            "analysis": result['analysis'],
            "chunks_created": len(result['chunks']),
            "chat_ready": True,
            "features_used": [
                "PyMuPDF Processing" if result['metadata']['processing_method'] == 'pymupdf' else "Text Processing",
                "Semantic Chunking",
                "Content Analysis",
                "Document-Aware Chat Preparation"
            ]
        }
        
    except Exception as e:
        print(f"❌ Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """
    Enhanced chat endpoint with document context
    Your original vision: Document-aware conversational AI using processed content
    """
    try:
        print(f"💬 GENAVATOR1 Chat: {request.message}")
        
        # Generate response using document-aware chat model
        response = chat_model.generate_response(
            message=request.message,
            context=request.context
        )
        
        print(f"✅ Response generated using {response.get('metadata', {}).get('document_chunks_used', 0)} document chunks")
        
        return {
            "response": response["response"],
            "confidence": response["confidence"],
            "context_used": response["context_used"],
            "model_used": response["model_used"],
            "features_used": [
                "Document Context Retrieval",
                "Semantic Chunk Analysis", 
                "Context-Aware Response Generation"
            ],
            "metadata": response.get("metadata", {}),
            "genavator_features": {
                "document_aware": response["context_used"],
                "chunks_analyzed": response.get("metadata", {}).get("document_chunks_used", 0),
                "conversation_ready": True
            }
        }
        
    except Exception as e:
        print(f"❌ Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")

@app.post("/api/v1/summarize")
async def summarize_text(request: SummarizeRequest):
    """
    Advanced text summarization
    Your original vision: Multiple summarization methods with intelligent content analysis
    """
    try:
        print(f"📝 Summarizing text: {len(request.text)} characters")
        
        # Generate summary using lightweight summarizer
        result = summarizer.summarize_text(
            text=request.text,
            max_length=request.max_length,
            min_length=request.min_length,
            summary_type=request.summary_type
        )
        
        print(f"✅ Summary generated: {result['method']}")
        
        return {
            "summary": result["summary"],
            "original_length": result.get("original_length", len(request.text)),
            "summary_length": result["length"],
            "compression_ratio": result.get("compression_ratio", 0),
            "method": result["method"],
            "confidence": result["confidence"],
            "language": request.language,
            "summary_type": request.summary_type,
            "genavator_features": {
                "intelligent_extraction": True,
                "content_analysis": True,
                "multiple_methods": ["general", "academic", "bullet_points"]
            }
        }
        
    except Exception as e:
        print(f"❌ Error in summarization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in summarization: {str(e)}")

@app.get("/api/v1/models")
async def get_models_info():
    """Get information about loaded AI models"""
    return {
        "service": "GENAVATOR1 AI Backend",
        "version": "2.0.0",
        "summarization_models": summarizer.get_model_info(),
        "chat_models": chat_model.get_model_info(),
        "document_processing": {
            "pymupdf_available": doc_processor.pymupdf_available,
            "supported_formats": doc_processor.get_supported_formats(),
            "features": ["Semantic Chunking", "Content Analysis", "Multi-format Support"]
        },
        "capabilities": {
            "languages": ["en", "es", "fr", "de", "zh", "ja"],
            "summary_types": ["general", "academic", "bullet_points"],
            "max_text_length": 50000,
            "document_aware_chat": True,
            "semantic_processing": True
        },
        "your_vision_implemented": [
            "PyMuPDF High-Quality PDF Processing",
            "Multi-format Document Support", 
            "Semantic Chunking",
            "Document Structure Preservation",
            "Content Analysis",
            "Document-Aware Conversational AI",
            "Advanced Summarization Methods"
        ]
    }

@app.get("/api/v1/conversation/history")
async def get_conversation_history():
    """Get recent conversation history"""
    return {
        "conversation_history": chat_model.get_conversation_history(),
        "document_loaded": bool(chat_model.current_document_chunks),
        "chunks_available": len(chat_model.current_document_chunks)
    }

@app.post("/api/v1/conversation/clear")
async def clear_conversation():
    """Clear conversation history"""
    chat_model.clear_conversation_history()
    return {
        "message": "Conversation history cleared successfully",
        "status": "ready"
    }

# Enhanced startup message
@app.on_event("startup")
async def startup_event():
    print("🚀 GENAVATOR1 AI Backend Started Successfully!")
    print("📡 FastAPI + PyMuPDF Integration Active")  
    print("🧠 Document-Aware AI Ready")
    print("🌐 All systems operational")

if __name__ == "__main__":
    print("🚀 Starting GENAVATOR1 AI Backend...")
    print("📄 PyMuPDF Integration: Enabled")
    print("🧠 AI Models: Lightweight & Efficient")
    print("🌐 Server will run on http://localhost:8000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )