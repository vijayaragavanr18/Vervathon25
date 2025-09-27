from typing import Dict, List, Optional, Any
import os
import tempfile
import json
import re
from pathlib import Path

class LightweightDocumentProcessor:
    """Lightweight document processor with PyMuPDF support when available"""
    
    def __init__(self):
        self.upload_dir = "uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Check for PyMuPDF availability
        self.pymupdf_available = False
        try:
            import fitz  # PyMuPDF
            self.pymupdf_available = True
            print("✅ PyMuPDF available for high-quality PDF processing")
        except ImportError:
            print("⚠️ PyMuPDF not available, using basic text processing")
    
    async def process_upload(self, file) -> Dict[str, Any]:
        """Process uploaded file and extract content"""
        try:
            # Read file content
            content = await file.read()
            filename = file.filename
            file_ext = filename.split('.')[-1].lower()
            
            # Save file
            file_path = os.path.join(self.upload_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Extract text based on file type
            text_content = ""
            
            if file_ext == 'pdf' and self.pymupdf_available:
                text_content = self._extract_pdf_pymupdf(file_path)
            elif file_ext in ['txt', 'md']:
                text_content = content.decode('utf-8', errors='ignore')
            elif file_ext == 'docx':
                text_content = self._extract_docx(file_path)
            elif file_ext == 'json':
                text_content = self._extract_json(file_path)
            elif file_ext == 'csv':
                text_content = self._extract_csv(file_path)
            else:
                text_content = f"File type '{file_ext}' - Content size: {len(content)} bytes"
            
            # Create semantic chunks
            chunks = self._create_semantic_chunks(text_content)
            
            # Generate analysis
            analysis = self._analyze_content(text_content)
            
            # Generate summary
            summary = self._generate_summary(text_content)
            
            return {
                'success': True,
                'filename': filename,
                'file_type': file_ext.upper(),
                'content': text_content,
                'chunks': chunks,
                'embeddings': None,  # Placeholder for future enhancement
                'summary': summary,
                'analysis': analysis,
                'metadata': {
                    'file_size': len(content),
                    'processing_method': 'pymupdf' if file_ext == 'pdf' and self.pymupdf_available else 'basic'
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error processing file: {str(e)}",
                'filename': file.filename if hasattr(file, 'filename') else 'unknown'
            }
    
    def _extract_pdf_pymupdf(self, file_path: str) -> str:
        """Extract text from PDF using PyMuPDF"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            text_content = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                text_content += f"\\n--- Page {page_num + 1} ---\\n{text}\\n"
            
            doc.close()
            return text_content
            
        except Exception as e:
            print(f"❌ PyMuPDF extraction failed: {e}")
            return f"PDF file - {os.path.basename(file_path)} (PyMuPDF extraction failed)"
    
    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX files"""
        try:
            # Try to use python-docx if available
            from docx import Document
            doc = Document(file_path)
            text = "\\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except ImportError:
            return f"DOCX file - {os.path.basename(file_path)} (python-docx not available)"
        except Exception as e:
            return f"DOCX file - {os.path.basename(file_path)} (extraction failed: {e})"
    
    def _extract_json(self, file_path: str) -> str:
        """Extract content from JSON files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert JSON to readable text
            if isinstance(data, dict):
                text_parts = []
                for key, value in data.items():
                    text_parts.append(f"{key}: {value}")
                return "\\n".join(text_parts)
            else:
                return json.dumps(data, indent=2)
                
        except Exception as e:
            return f"JSON file - {os.path.basename(file_path)} (extraction failed: {e})"
    
    def _extract_csv(self, file_path: str) -> str:
        """Extract content from CSV files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Convert CSV to more readable format
            lines = content.split('\\n')
            if lines and len(lines) > 1:
                header = lines[0]
                text = f"CSV Data with columns: {header}\\n"
                text += f"Total rows: {len(lines) - 1}\\n"
                text += f"Sample data:\\n{content[:500]}..."
                return text
            else:
                return content
                
        except Exception as e:
            return f"CSV file - {os.path.basename(file_path)} (extraction failed: {e})"
    
    def _create_semantic_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Create semantic chunks from text"""
        if len(text) <= chunk_size:
            return [text]
        
        # Split by paragraphs first, then by sentences
        paragraphs = text.split('\\n\\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) <= chunk_size:
                current_chunk += paragraph + "\\n\\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\\n\\n"
        
        # Add remaining content
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If chunks are still too large, split by sentences
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= chunk_size:
                final_chunks.append(chunk)
            else:
                # Split by sentences
                sentences = re.split(r'[.!?]+', chunk)
                current_sentence_chunk = ""
                
                for sentence in sentences:
                    if len(current_sentence_chunk) + len(sentence) <= chunk_size:
                        current_sentence_chunk += sentence + ". "
                    else:
                        if current_sentence_chunk:
                            final_chunks.append(current_sentence_chunk.strip())
                        current_sentence_chunk = sentence + ". "
                
                if current_sentence_chunk:
                    final_chunks.append(current_sentence_chunk.strip())
        
        return final_chunks
    
    def _analyze_content(self, text: str) -> Dict[str, Any]:
        """Analyze text content and extract key metrics"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        paragraphs = text.split('\\n\\n')
        
        # Extract key phrases (simple approach)
        word_freq = {}
        for word in words:
            clean_word = re.sub(r'[^\\w]', '', word.lower())
            if len(clean_word) > 3:  # Only consider words longer than 3 characters
                word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
        
        # Get most frequent words as keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'paragraph_count': len([p for p in paragraphs if p.strip()]),
            'character_count': len(text),
            'keywords': [word for word, freq in keywords],
            'avg_words_per_sentence': len(words) / max(len(sentences), 1),
            'readability_score': self._calculate_readability(words, sentences)
        }
    
    def _calculate_readability(self, words: List[str], sentences: List[str]) -> float:
        """Calculate simple readability score"""
        if not words or not sentences:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Simple readability formula (lower is easier)
        score = (avg_sentence_length * 0.39) + (avg_word_length * 11.8) - 15.59
        return max(0, min(100, score))
    
    def _generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """Generate simple extractive summary"""
        if not text:
            return "No content to summarize."
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
        
        if not sentences:
            return "Document processed successfully."
        
        # Take first few sentences as summary
        summary_sentences = sentences[:max_sentences]
        summary = '. '.join(summary_sentences)
        
        if not summary.endswith('.'):
            summary += '.'
        
        return summary
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        formats = ['TXT', 'MD', 'JSON', 'CSV']
        
        if self.pymupdf_available:
            formats.append('PDF')
        
        try:
            import docx
            formats.append('DOCX')
        except ImportError:
            pass
        
        return formats