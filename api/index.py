"""
Vercel-compatible FastAPI application for RAG functionality
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import tempfile
import sqlite3
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GENAVATOR1 RAG Backend",
    description="RAG-powered AI service with document processing",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # More permissive for deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy loading for heavy dependencies
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

def get_sentence_model():
    """Lazy load sentence transformer model"""
    global sentence_model
    if sentence_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Sentence transformer loaded")
        except ImportError:
            logger.error("❌ sentence_transformers not installed")
            raise HTTPException(status_code=500, detail="sentence_transformers package not available")
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            raise HTTPException(status_code=500, detail=f"Model loading failed: {str(e)}")
    return sentence_model

def get_database():
    """Initialize database connection"""
    global db_connection
    if db_connection is None:
        try:
            # Use /tmp directory for Vercel
            db_path = "/tmp/rag_documents.db"
            db_connection = sqlite3.connect(db_path, check_same_thread=False)
            
            cursor = db_connection.cursor()
            
            # Create tables
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
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")
    
    return db_connection

def extract_text_from_document(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
    """Extract text from various document types"""
    file_extension = os.path.splitext(filename.lower())[1]
    
    try:
        if file_extension == '.pdf':
            try:
                import fitz  # PyMuPDF
            except ImportError:
                raise HTTPException(status_code=500, detail="PyMuPDF not installed")
                
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name
            
            try:
                doc = fitz.open(tmp_path)
                pages_content = []
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    
                    if text.strip():
                        pages_content.append({
                            'page_number': page_num + 1,
                            'content': text.strip(),
                            'char_count': len(text)
                        })
                
                doc.close()
                return pages_content
            finally:
                os.unlink(tmp_path)
                
        elif file_extension == '.docx':
            try:
                from docx import Document
            except ImportError:
                raise HTTPException(status_code=500, detail="python-docx not installed")
                
            import io
            
            doc = Document(io.BytesIO(file_content))
            full_text = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    full_text.append(paragraph.text.strip())
            
            if full_text:
                combined_text = '\n'.join(full_text)
                return [{
                    'page_number': 1,
                    'content': combined_text,
                    'char_count': len(combined_text)
                }]
                
        elif file_extension == '.txt':
            try:
                content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                content = file_content.decode('latin-1')
            
            if content.strip():
                return [{
                    'page_number': 1,
                    'content': content.strip(),
                    'char_count': len(content)
                }]
        
        return []
        
    except Exception as e:
        logger.error(f"Text extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"Text extraction failed: {str(e)}")

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip())
    
    return chunks

def create_embeddings(texts: List[str]) -> Any:
    """Create embeddings for text chunks"""
    try:
        model = get_sentence_model()
        embeddings = model.encode(texts, convert_to_tensor=False)
        return embeddings
    except Exception as e:
        logger.error(f"Embedding creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding creation failed: {str(e)}")

def save_document_to_db(document_id: str, filename: str, file_size: int, file_type: str,
                       chunks: List[str], page_numbers: List[int], embeddings: Any):
    """Save document and chunks to database"""
    try:
        db = get_database()
        cursor = db.cursor()
        
        cursor.execute('''
            INSERT INTO documents (id, filename, total_chunks, file_size, file_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (document_id, filename, len(chunks), file_size, file_type))
        
        for i, (chunk, page_num, embedding) in enumerate(zip(chunks, page_numbers, embeddings)):
            embedding_blob = embedding.tobytes()
            cursor.execute('''
                INSERT INTO document_chunks 
                (document_id, chunk_index, content, page_number, embedding, chunk_size)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (document_id, i, chunk, page_num, embedding_blob, len(chunk)))
        
        db.commit()
        logger.info(f"✅ Document saved: {len(chunks)} chunks")
        
    except Exception as e:
        logger.error(f"Database save error: {e}")
        raise HTTPException(status_code=500, detail=f"Database save failed: {str(e)}")

def search_similar_chunks(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search for similar document chunks"""
    try:
        model = get_sentence_model()
        query_embedding = model.encode([query])
        
        db = get_database()
        cursor = db.cursor()
        cursor.execute('''
            SELECT dc.content, dc.page_number, dc.embedding, d.filename, dc.document_id
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
        ''')
        
        results = cursor.fetchall()
        if not results:
            return []
        
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        
        similarities = []
        for content, page_num, embedding_blob, filename, doc_id in results:
            embedding = np.frombuffer(embedding_blob, dtype=np.float32)
            embedding = embedding.reshape(1, -1)
            
            similarity = cosine_similarity(query_embedding, embedding)[0][0]
            
            similarities.append({
                'content': content,
                'page_number': page_num,
                'filename': filename,
                'document_id': doc_id,
                'similarity': float(similarity)
            })
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []

def generate_rag_response(query: str, relevant_chunks: List[Dict[str, Any]]) -> str:
    """Generate response based on retrieved chunks"""
    if not relevant_chunks:
        return "I don't have information about that topic in the uploaded documents. Please upload relevant documents first."
    
    context_parts = []
    for chunk in relevant_chunks[:3]:
        context_parts.append(f"From {chunk['filename']} (Page {chunk['page_number']}): {chunk['content'][:300]}...")
    
    context = "\n\n".join(context_parts)
    
    if "what" in query.lower() or "define" in query.lower() or "explain" in query.lower():
        response = f"Based on your uploaded documents:\n\n{context}\n\nSource: {len(relevant_chunks)} relevant sections."
    elif "how" in query.lower():
        response = f"Here's how based on your documents:\n\n{context}\n\nFrom {len(relevant_chunks)} sections."
    elif "why" in query.lower():
        response = f"The reason according to your documents:\n\n{context}\n\nFrom {len(relevant_chunks)} sections."
    else:
        response = f"Regarding '{query}':\n\n{context}\n\nSource: {len(relevant_chunks)} sections."
    
    return response

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GENAVATOR1 RAG Backend",
        "status": "online",
        "version": "2.0.0-vercel",
        "features": ["document_upload", "rag_search", "serverless"]
    }

@app.get("/api/v1/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "platform": "vercel"
    }

@app.post("/api/v1/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document"""
    try:
        logger.info(f"📄 Processing: {file.filename}")
        
        # Validate file type
        supported_extensions = ['.pdf', '.docx', '.txt']
        file_extension = os.path.splitext(file.filename.lower())[1]
        if file_extension not in supported_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Create document ID
        document_id = f"doc_{int(datetime.now().timestamp())}_{file.filename.replace('.', '_').replace(' ', '_')}"
        
        # Extract text
        pages_content = extract_text_from_document(file_content, file.filename)
        
        if not pages_content:
            raise HTTPException(status_code=400, detail="No text content found")
        
        # Create chunks
        all_chunks = []
        chunk_page_numbers = []
        
        for page_data in pages_content:
            page_chunks = chunk_text(page_data['content'])
            all_chunks.extend(page_chunks)
            chunk_page_numbers.extend([page_data['page_number']] * len(page_chunks))
        
        if not all_chunks:
            raise HTTPException(status_code=400, detail="Could not create chunks")
        
        logger.info(f"📝 Created {len(all_chunks)} chunks")
        
        # Create embeddings
        embeddings = create_embeddings(all_chunks)
        
        # Save to database
        save_document_to_db(
            document_id, file.filename, file_size, file.content_type,
            all_chunks, chunk_page_numbers, embeddings
        )
        
        return DocumentResponse(
            success=True,
            filename=file.filename,
            document_id=document_id,
            chunks_created=len(all_chunks),
            message=f"Successfully processed! Created {len(all_chunks)} searchable chunks."
        )
        
    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_with_documents(request: ChatRequest):
    """Chat with documents using RAG"""
    try:
        logger.info(f"💬 Query: {request.message}")
        
        relevant_chunks = search_similar_chunks(request.message, top_k=5)
        response = generate_rag_response(request.message, relevant_chunks)
        document_sources = list(set([chunk['filename'] for chunk in relevant_chunks]))
        
        import numpy as np
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
    """List uploaded documents"""
    try:
        db = get_database()
        cursor = db.cursor()
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

# Export app for Vercel
handler = app