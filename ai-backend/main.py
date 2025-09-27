from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import tempfile
from typing import List, Optional
import json

# Import our enhanced services
from summarizer import DocumentSummarizer
from document_chat_model import DocumentAwareChatModel
from advanced_document_processor import AdvancedDocumentProcessor

# Initialize FastAPI app
app = FastAPI(
    title="GENAVATOR1 AI Backend",
    description="Hugging Face powered AI service for document summarization and chat",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI models
print("🤖 Loading enhanced AI models...")
summarizer = DocumentSummarizer()
chat_model = DocumentAwareChatModel()
doc_processor = AdvancedDocumentProcessor()
print("✅ Enhanced AI models loaded successfully!")

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

class ChatResponse(BaseModel):
    response: str
    emotion: str = "neutral"
    confidence: float
    model_used: str = "document_aware_chat"
    document_context_used: bool = False
    relevant_chunks: int = 0

class SummaryResponse(BaseModel):
    summary: str
    key_points: List[str]
    word_count: int
    original_length: int
    compression_ratio: float

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "GENAVATOR1 AI Backend",
        "models_loaded": {
            "summarizer": summarizer.is_loaded(),
            "chat_model": chat_model.is_loaded()
        },
        "timestamp": "2025-09-27"
    }

# Advanced Document upload and processing
@app.post("/api/v1/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document with PyMuPDF + semantic chunking"""
    try:
        print(f"📄 Processing document: {file.filename}")
        
        # Process document with advanced processor
        result = await doc_processor.process_upload(file)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Processing failed'))
        
        # Load document context into chat model for RAG
        chat_model.load_document_context(
            chunks=result['chunks'],
            embeddings=result['embeddings'],
            metadata={
                'filename': result['filename'],
                'file_type': result['file_type'],
                'word_count': result['analysis']['word_count'],
                'content_type': result['analysis']['content_type']
            }
        )
        
        # Generate enhanced summary
        content = result['content']
        quick_summary = summarizer.summarize(content[:2000] if len(content) > 2000 else content, max_length=150)
        
        return {
            "success": True,
            "filename": result['filename'],
            "file_size": result['size'],
            "file_type": result['file_type'],
            "extraction_method": result['extraction_method'],
            "pages": result.get('pages', 1),
            "content_preview": content[:400] + "..." if len(content) > 400 else content,
            "quick_summary": quick_summary,
            "analysis": result['analysis'],
            "chunks_created": len(result['chunks']),
            "ready_for_chat": True,
            "semantic_search_enabled": len(result['embeddings']) > 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

# Summarization endpoint
@app.post("/api/v1/summarize", response_model=SummaryResponse)
async def summarize_text(request: SummarizeRequest):
    """Generate AI-powered summary using Hugging Face models"""
    try:
        print(f"📝 Generating {request.summary_type} summary...")
        
        # Generate summary based on type
        if request.summary_type == "academic":
            summary = summarizer.academic_summary(request.text, request.max_length)
        elif request.summary_type == "bullet_points":
            summary = summarizer.bullet_point_summary(request.text)
        else:
            summary = summarizer.summarize(request.text, request.max_length, request.min_length)
        
        # Extract key points
        key_points = summarizer.extract_key_points(request.text)
        
        # Calculate metrics
        original_words = len(request.text.split())
        summary_words = len(summary.split())
        compression_ratio = round((original_words - summary_words) / original_words * 100, 2)
        
        return SummaryResponse(
            summary=summary,
            key_points=key_points,
            word_count=summary_words,
            original_length=original_words,
            compression_ratio=compression_ratio
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

# Enhanced Document-Aware Chat endpoint
@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_with_document(request: ChatRequest):
    """AI Chat with document context using advanced RAG"""
    try:
        print(f"💬 Processing document-aware chat in {request.language}...")
        
        # Generate response using document-aware model
        response_data = chat_model.generate_response(
            message=request.message,
            use_document_context=True,
            max_context_chunks=3,
            temperature=0.7
        )
        
        return ChatResponse(
            response=response_data["response"],
            emotion=response_data.get("emotion", "neutral"),
            confidence=response_data.get("confidence", 0.95),
            model_used=response_data.get("model_used", "document_aware_chat"),
            document_context_used=response_data.get("document_context_used", False),
            relevant_chunks=response_data.get("relevant_chunks", 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document chat failed: {str(e)}")

# Batch document analysis
@app.post("/api/v1/analyze-batch")
async def analyze_multiple_documents(files: List[UploadFile] = File(...)):
    """Analyze multiple documents and create comprehensive summary"""
    try:
        results = []
        combined_text = ""
        
        for file in files:
            # Process each document
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            # Extract text
            text = doc_processor.extract_text(tmp_file_path, file.content_type)
            combined_text += f"\n\n--- {file.filename} ---\n{text}"
            
            # Individual summary
            individual_summary = summarizer.summarize(text, max_length=100)
            
            results.append({
                "filename": file.filename,
                "word_count": len(text.split()),
                "summary": individual_summary
            })
            
            # Clean up
            os.unlink(tmp_file_path)
        
        # Generate combined summary
        combined_summary = summarizer.summarize(combined_text, max_length=300)
        key_themes = summarizer.extract_key_points(combined_text)
        
        return {
            "success": True,
            "individual_results": results,
            "combined_analysis": {
                "comprehensive_summary": combined_summary,
                "key_themes": key_themes,
                "total_documents": len(files),
                "total_words": len(combined_text.split())
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

# Get available models info
@app.get("/api/v1/models")
async def get_model_info():
    """Get information about loaded AI models"""
    return {
        "summarization_models": summarizer.get_model_info(),
        "chat_models": chat_model.get_model_info(),
        "capabilities": {
            "languages": ["en", "es", "fr", "de", "zh", "ja"],
            "summary_types": ["general", "academic", "bullet_points"],
            "max_text_length": 10000,
            "supported_formats": ["PDF", "DOCX", "TXT"]
        }
    }

# Run the server
if __name__ == "__main__":
    print("🚀 Starting GENAVATOR1 AI Backend...")
    print("📡 FastAPI + Hugging Face Integration")
    print("🌐 CORS enabled for frontend integration")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )