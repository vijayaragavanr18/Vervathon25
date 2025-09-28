"""
Complete RAG-based FastAPI Backend for Document Q&A
Uses PyMuPDF for document processing and vector embeddings for semantic search
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import tempfile
import sqlite3
from typing import List, Optional, Dict, Any
import json
import fitz  # PyMuPDF
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GENAVATOR1 RAG Backend",
    description="RAG-powered AI service with PyMuPDF and vector search",
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

# Global variables for models and database
sentence_model = None
db_connection = None

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = ""
    language: str = "en"
    conversation_history: List[dict] = []

class DocumentResponse(BaseModel):
    success: bool
    filename: str
    document_id: str
    chunks_created: int
    message: str

class ChatResponse(BaseModel):
    response: str
    relevant_chunks: List[Dict[str, Any]]
    confidence: float
    document_sources: List[str]

def initialize_models():
    """Initialize sentence transformer model"""
    global sentence_model
    try:
        logger.info("🤖 Loading sentence transformer model...")
        if SentenceTransformer is None:
            raise ImportError("sentence_transformers not available")
        sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Sentence transformer loaded successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Error loading models: {e}")
        return False

def initialize_database():
    """Initialize SQLite database for document storage"""
    global db_connection
    try:
        db_path = "rag_documents.db"
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
        
        # Create tables
        cursor = db_connection.cursor()
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_chunks INTEGER,
                file_size INTEGER,
                file_type TEXT
            )
        ''')
        
        # Document chunks table with embeddings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT,
                chunk_index INTEGER,
                content TEXT,
                page_number INTEGER,
                embedding BLOB,
                chunk_size INTEGER,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        ''')
        
        db_connection.commit()
        logger.info("✅ Database initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
        return False

def extract_text_from_pdf(file_path: str) -> List[Dict[str, Any]]:
    """Extract text from PDF using PyMuPDF with page information"""
    try:
        doc = fitz.open(file_path)
        pages_content = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            if text.strip():  # Only add non-empty pages
                pages_content.append({
                    'page_number': page_num + 1,
                    'content': text.strip(),
                    'char_count': len(text)
                })
        
        doc.close()
        return pages_content
        
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"PDF processing failed: {str(e)}")

def extract_text_from_docx(file_path: str) -> List[Dict[str, Any]]:
    """Extract text from DOCX files"""
    try:
        try:
            from docx import Document
        except ImportError:
            raise HTTPException(status_code=500, detail="python-docx not installed")
            
        doc = Document(file_path)
        
        content = []
        current_page = 1
        
        # Extract all paragraphs
        full_text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                full_text.append(paragraph.text.strip())
        
        if full_text:
            # Combine all text and treat as single page for DOCX
            combined_text = '\n'.join(full_text)
            content.append({
                'page_number': 1,
                'content': combined_text,
                'char_count': len(combined_text)
            })
        
        return content
        
    except ImportError:
        raise HTTPException(status_code=500, detail="python-docx package not installed. Please install it to process DOCX files.")
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"DOCX processing failed: {str(e)}")

def extract_text_from_txt(file_path: str) -> List[Dict[str, Any]]:
    """Extract text from TXT files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        if content.strip():
            return [{
                'page_number': 1,
                'content': content.strip(),
                'char_count': len(content)
            }]
        else:
            return []
            
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                content = file.read()
            return [{
                'page_number': 1,
                'content': content.strip(),
                'char_count': len(content)
            }]
        except Exception as e:
            logger.error(f"TXT extraction error: {e}")
            raise HTTPException(status_code=400, detail=f"TXT processing failed: {str(e)}")
    except Exception as e:
        logger.error(f"TXT extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"TXT processing failed: {str(e)}")

def extract_text_from_document(file_path: str, file_extension: str) -> List[Dict[str, Any]]:
    """Extract text from various document types"""
    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == '.docx':
        return extract_text_from_docx(file_path)
    elif file_extension == '.txt':
        return extract_text_from_txt(file_path)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {file_extension}")

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks for better context preservation"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip())
    
    return chunks

def create_embeddings(texts: List[str]) -> np.ndarray:
    """Create embeddings for text chunks"""
    try:
        embeddings = sentence_model.encode(texts, convert_to_tensor=False)
        return embeddings
    except Exception as e:
        logger.error(f"Embedding creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding creation failed: {str(e)}")

def save_document_to_db(document_id: str, filename: str, file_size: int, file_type: str,
                       chunks: List[str], page_numbers: List[int], embeddings: np.ndarray):
    """Save document and its chunks with embeddings to database"""
    try:
        cursor = db_connection.cursor()
        
        # Save document metadata
        cursor.execute('''
            INSERT INTO documents (id, filename, total_chunks, file_size, file_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (document_id, filename, len(chunks), file_size, file_type))
        
        # Save chunks with embeddings
        for i, (chunk, page_num, embedding) in enumerate(zip(chunks, page_numbers, embeddings)):
            embedding_blob = embedding.tobytes()
            cursor.execute('''
                INSERT INTO document_chunks 
                (document_id, chunk_index, content, page_number, embedding, chunk_size)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (document_id, i, chunk, page_num, embedding_blob, len(chunk)))
        
        db_connection.commit()
        logger.info(f"✅ Document {filename} saved to database with {len(chunks)} chunks")
        
    except Exception as e:
        logger.error(f"Database save error: {e}")
        raise HTTPException(status_code=500, detail=f"Database save failed: {str(e)}")

def search_similar_chunks(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search for similar document chunks using cosine similarity"""
    try:
        # Create query embedding
        query_embedding = sentence_model.encode([query])
        
        # Get all chunks from database
        cursor = db_connection.cursor()
        cursor.execute('''
            SELECT dc.content, dc.page_number, dc.embedding, d.filename, dc.document_id
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
        ''')
        
        results = cursor.fetchall()
        if not results:
            return []
        
        # Calculate similarities
        similarities = []
        for content, page_num, embedding_blob, filename, doc_id in results:
            # Convert blob back to numpy array
            embedding = np.frombuffer(embedding_blob, dtype=np.float32)
            embedding = embedding.reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, embedding)[0][0]
            
            similarities.append({
                'content': content,
                'page_number': page_num,
                'filename': filename,
                'document_id': doc_id,
                'similarity': float(similarity)
            })
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []

def generate_rag_response(query: str, relevant_chunks: List[Dict[str, Any]]) -> str:
    """Generate response based on retrieved chunks (simple template-based for now)"""
    if not relevant_chunks:
        return "I don't have information about that topic in the uploaded documents. Could you please upload relevant documents first?"
    
    # Create context from relevant chunks
    context_parts = []
    for chunk in relevant_chunks[:3]:  # Use top 3 most relevant chunks
        context_parts.append(f"From {chunk['filename']} (Page {chunk['page_number']}): {chunk['content'][:300]}...")
    
    context = "\n\n".join(context_parts)
    
    # Simple template-based response
    if "what" in query.lower() or "define" in query.lower() or "explain" in query.lower():
        response = f"Based on your uploaded documents, here's what I found:\n\n{context}\n\nThis information comes from {len(relevant_chunks)} relevant sections in your documents."
    elif "how" in query.lower():
        response = f"Here's how to approach this based on your documents:\n\n{context}\n\nI found this information across {len(relevant_chunks)} sections of your uploaded materials."
    elif "why" in query.lower():
        response = f"The reason appears to be:\n\n{context}\n\nThis explanation is compiled from {len(relevant_chunks)} relevant parts of your documents."
    else:
        response = f"Regarding your question about '{query}', here's what I found in your documents:\n\n{context}\n\nSource: {len(relevant_chunks)} relevant sections from your uploaded files."
    
    return response

# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize models and database on startup"""
    logger.info("🚀 Starting GENAVATOR1 RAG Backend...")
    
    if not initialize_models():
        raise Exception("Failed to initialize models")
    
    if not initialize_database():
        raise Exception("Failed to initialize database")
    
    logger.info("✅ RAG Backend startup complete!")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GENAVATOR1 RAG Backend is running!",
        "status": "online",
        "version": "2.0.0",
        "features": ["document_upload", "rag_search", "vector_embeddings", "pymupdf_processing"]
    }

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_loaded": sentence_model is not None,
        "database_connected": db_connection is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document with RAG pipeline"""
    try:
        logger.info(f"📄 Processing upload: {file.filename}")
        
        # Validate file type
        supported_extensions = ['.pdf', '.docx', '.txt']
        file_extension = os.path.splitext(file.filename.lower())[1]
        if file_extension not in supported_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported formats: {', '.join(supported_extensions)}")
        
        # Create document ID
        document_id = f"doc_{int(datetime.now().timestamp())}_{file.filename.replace('.', '_').replace(' ', '_')}"
        
        # Create uploads directory
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save uploaded file temporarily
        file_extension = os.path.splitext(file.filename.lower())[1]
        file_path = os.path.join(upload_dir, f"{document_id}{file_extension}")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            file_size = len(content)
        
        # Extract text based on file type
        logger.info(f"📖 Extracting text from {file.filename} ({file_extension})")
        pages_content = extract_text_from_document(file_path, file_extension)
        
        if not pages_content:
            raise HTTPException(status_code=400, detail="No text content found in the PDF")
        
        # Create chunks from all pages
        all_chunks = []
        chunk_page_numbers = []
        
        for page_data in pages_content:
            page_chunks = chunk_text(page_data['content'])
            all_chunks.extend(page_chunks)
            chunk_page_numbers.extend([page_data['page_number']] * len(page_chunks))
        
        if not all_chunks:
            raise HTTPException(status_code=400, detail="Could not create chunks from document")
        
        logger.info(f"📝 Created {len(all_chunks)} chunks from {len(pages_content)} pages")
        
        # Create embeddings
        logger.info("🧠 Creating embeddings...")
        embeddings = create_embeddings(all_chunks)
        
        # Save to database
        logger.info("💾 Saving to database...")
        save_document_to_db(
            document_id, file.filename, file_size, file.content_type,
            all_chunks, chunk_page_numbers, embeddings
        )
        
        # Clean up temporary file
        os.remove(file_path)
        
        return DocumentResponse(
            success=True,
            filename=file.filename,
            document_id=document_id,
            chunks_created=len(all_chunks),
            message=f"Document processed successfully! Created {len(all_chunks)} searchable chunks from {len(pages_content)} pages."
        )
        
    except Exception as e:
        logger.error(f"❌ Upload processing error: {e}")
        # Clean up on error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_with_documents(request: ChatRequest):
    """Chat endpoint with RAG-based document search"""
    try:
        logger.info(f"💬 Processing query: {request.message}")
        
        # Search for relevant document chunks
        relevant_chunks = search_similar_chunks(request.message, top_k=5)
        
        # Generate response using RAG
        response = generate_rag_response(request.message, relevant_chunks)
        
        # Extract unique document sources
        document_sources = list(set([chunk['filename'] for chunk in relevant_chunks]))
        
        # Calculate average confidence from similarities
        avg_confidence = np.mean([chunk['similarity'] for chunk in relevant_chunks]) if relevant_chunks else 0.0
        
        return ChatResponse(
            response=response,
            relevant_chunks=relevant_chunks,
            confidence=float(avg_confidence),
            document_sources=document_sources
        )
        
    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        cursor = db_connection.cursor()
        cursor.execute('''
            SELECT id, filename, upload_date, total_chunks, file_size, file_type
            FROM documents
            ORDER BY upload_date DESC
        ''')
        
        documents = []
        for row in cursor.fetchall():
            documents.append({
                'id': row[0],
                'filename': row[1],
                'upload_date': row[2],
                'total_chunks': row[3],
                'file_size': row[4],
                'file_type': row[5]
            })
        
        return {"documents": documents, "count": len(documents)}
        
    except Exception as e:
        logger.error(f"❌ Document listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting GENAVATOR1 RAG Backend...")
    print("📡 FastAPI + PyMuPDF + RAG")
    print("🌐 Server will run on http://localhost:8001")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )