from typing import List, Dict, Optional
import re
import json
import logging
import os

class DocumentAwareChatModel:
    """Lightweight conversational AI that can chat with document content"""
    
    def __init__(self):
        # Simple chat model without heavy dependencies
        self.current_model_name = "basic-chat"
        self.current_document_chunks = []
        self.current_document_metadata = {}
        
        # Conversation context
        self.conversation_history = []
        self.max_context_length = 1000
        self.max_response_length = 150
        
        print("✅ Lightweight chat model initialized!")
    
    def load_document_context(self, chunks: List[str], embeddings=None, metadata: Dict = {}):
        """Load document chunks and metadata for context-aware responses"""
        self.current_document_chunks = chunks
        self.current_document_metadata = metadata
        print(f"📚 Loaded {len(chunks)} document chunks for context")
    
    def _get_relevant_context(self, query: str, max_chunks: int = 3) -> str:
        """Get relevant document chunks based on simple keyword matching"""
        if not self.current_document_chunks:
            return ""
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Score chunks based on keyword overlap
        chunk_scores = []
        for i, chunk in enumerate(self.current_document_chunks):
            chunk_lower = chunk.lower()
            chunk_words = set(chunk_lower.split())
            
            # Calculate simple overlap score
            overlap = len(query_words.intersection(chunk_words))
            score = overlap / len(query_words) if query_words else 0
            
            chunk_scores.append((score, i, chunk))
        
        # Sort by score and get top chunks
        chunk_scores.sort(reverse=True, key=lambda x: x[0])
        relevant_chunks = [chunk for _, _, chunk in chunk_scores[:max_chunks] if chunk_scores[0][0] > 0]
        
        return "\n\n".join(relevant_chunks)
    
    def generate_response(self, message: str, context: str = "", max_length: int = None) -> Dict:
        """Generate response with document context"""
        try:
            if max_length is None:
                max_length = self.max_response_length
            
            # Get relevant document context
            doc_context = self._get_relevant_context(message)
            combined_context = f"{context}\n{doc_context}".strip()
            
            # Generate response based on message content and context
            response = self._generate_contextual_response(message, combined_context)
            
            # Update conversation history
            self.conversation_history.append({
                "user": message,
                "assistant": response,
                "context_used": bool(combined_context)
            })
            
            # Keep history manageable
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return {
                "response": response,
                "confidence": 0.85,
                "context_used": bool(combined_context),
                "model_used": self.current_model_name,
                "metadata": {
                    "context_length": len(combined_context),
                    "document_chunks_used": len(doc_context.split('\n\n')) if doc_context else 0
                }
            }
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return {
                "response": "I apologize, but I encountered an error while processing your message. Please try again.",
                "confidence": 0.0,
                "context_used": False,
                "error": str(e)
            }
    
    def _generate_contextual_response(self, message: str, context: str) -> str:
        """Generate response based on message and context"""
        message_lower = message.lower()
        
        # Document-specific responses
        if context:
            if "summary" in message_lower or "summarize" in message_lower:
                return f"Based on the document content, here's a summary: {context[:200]}..." if len(context) > 200 else f"Here's a summary of the document: {context}"
            
            elif "what" in message_lower and ("is" in message_lower or "are" in message_lower):
                return f"According to the document: {context[:300]}..." if len(context) > 300 else f"Based on the document: {context}"
            
            elif "how" in message_lower:
                return f"The document explains that {context[:250]}..." if len(context) > 250 else f"According to the document: {context}"
            
            elif "why" in message_lower:
                return f"The document indicates that {context[:250]}..." if len(context) > 250 else f"Based on the document: {context}"
            
            elif "where" in message_lower:
                return f"The document mentions: {context[:250]}..." if len(context) > 250 else f"According to the document: {context}"
            
            else:
                return f"Based on the document content related to your question: {context[:300]}..." if len(context) > 300 else f"Regarding your question, the document states: {context}"
        
        # General responses without document context
        elif "hello" in message_lower or "hi" in message_lower:
            return "Hello! I'm your AI assistant. I can help you analyze documents, answer questions, and provide summaries. Please upload a document to get started!"
        
        elif "how are you" in message_lower:
            return "I'm doing well, thank you! I'm ready to help you with document analysis and answering questions about your uploaded content."
        
        elif "help" in message_lower:
            return "I can help you with: 1) Analyzing uploaded documents, 2) Answering questions about document content, 3) Creating summaries, 4) Finding specific information in your documents. Just upload a document and ask me questions about it!"
        
        elif "thank" in message_lower:
            return "You're welcome! I'm here to help you with any document-related questions or analysis you need."
        
        else:
            return f"I understand you're asking about '{message}'. To provide the most accurate answer, please upload a document so I can give you specific information based on the content."
    
    def get_conversation_history(self) -> List[Dict]:
        """Get recent conversation history"""
        return self.conversation_history[-5:]  # Return last 5 exchanges
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("🗑️ Conversation history cleared")
    
    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        return {
            "name": self.current_model_name,
            "type": "lightweight-chat",
            "capabilities": ["document-aware-chat", "context-retrieval", "conversation-history"],
            "status": "ready",
            "document_loaded": bool(self.current_document_chunks),
            "chunks_available": len(self.current_document_chunks)
        }
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to a different model (placeholder for future expansion)"""
        print(f"📝 Model switching requested: {model_name}")
        return True  # Always successful for basic model