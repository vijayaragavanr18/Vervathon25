from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
from typing import List, Dict, Optional
import re
import json
import logging
from sentence_transformers import SentenceTransformer
import numpy as np

class DocumentAwareChatModel:
    """Advanced conversational AI that can chat with document content using RAG"""
    
    def __init__(self):
        # Model configurations for different use cases
        self.chat_models = {
            'microsoft/DialoGPT-medium': 'Conversational',
            'facebook/blenderbot-400M-distill': 'General Chat',
            'microsoft/DialoGPT-small': 'Fast Response',
            'facebook/blenderbot-1B-distill': 'Advanced Chat (Slow)'
        }
        
        # Default model (balanced performance/speed)
        self.current_model_name = "microsoft/DialoGPT-medium"
        self.chat_pipeline = None
        self.tokenizer = None
        self.model = None
        
        # For document retrieval
        self.embedder = None
        self.current_document_chunks = []
        self.current_document_embeddings = []
        self.current_document_metadata = {}
        
        # Conversation context
        self.conversation_history = []
        self.max_context_length = 1000
        self.max_response_length = 150
        
        self.device = 0 if torch.cuda.is_available() else -1
        print(f"🎯 Using device: {'GPU' if self.device >= 0 else 'CPU'}")
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize chat and embedding models"""
        try:
            print("📥 Loading conversational AI models...")
            
            # Load sentence transformer for document retrieval
            try:
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ Sentence transformer loaded for document retrieval")
            except Exception as e:
                print(f"⚠️ Could not load sentence transformer: {e}")
                self.embedder = None
            
            # Load chat model
            self._load_chat_model(self.current_model_name)
            
        except Exception as e:
            print(f"❌ Error initializing models: {e}")
            self.chat_pipeline = None
            self.model = None
            self.tokenizer = None
    
    def _load_chat_model(self, model_name: str):
        """Load specific chat model"""
        try:
            print(f"📥 Loading chat model: {model_name}")
            
            if "DialoGPT" in model_name:
                # Use DialoGPT for conversational AI
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForCausalLM.from_pretrained(model_name)
                
                # Add padding token if it doesn't exist
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                self.chat_pipeline = None  # We'll use model directly
                self.current_model_name = model_name
                print(f"✅ DialoGPT model loaded successfully!")
                
            else:
                # Use pipeline for other models
                self.chat_pipeline = pipeline(
                    "text-generation" if "blenderbot" not in model_name.lower() else "conversational",
                    model=model_name,
                    device=self.device,
                    tokenizer_kwargs={"padding": True, "truncation": True}
                )
                self.current_model_name = model_name
                print(f"✅ Chat model {model_name} loaded successfully!")
                
        except Exception as e:
            print(f"⚠️ Failed to load {model_name}: {e}")
            print("🔄 Using fallback conversation system...")
            self.chat_pipeline = None
            self.model = None
            self.tokenizer = None
    
    def load_document_context(self, chunks: List[Dict], embeddings: List[List[float]], metadata: Dict):
        """Load document context for RAG-based conversations"""
        self.current_document_chunks = chunks
        self.current_document_embeddings = embeddings
        self.current_document_metadata = metadata
        
        print(f"📄 Document loaded: {metadata.get('filename', 'Unknown')}")
        print(f"📊 {len(chunks)} chunks available for conversation")
        
        # Reset conversation history when new document is loaded
        self.conversation_history = []
    
    def generate_response(self, 
                         message: str, 
                         use_document_context: bool = True,
                         max_context_chunks: int = 3,
                         temperature: float = 0.7) -> Dict:
        """Generate response using document context and conversation history"""
        
        try:
            # Get relevant document context
            document_context = ""
            relevant_chunks = []
            
            if use_document_context and self.current_document_chunks and self.embedder:
                relevant_chunks = self._get_relevant_context(message, max_context_chunks)
                if relevant_chunks:
                    context_texts = [chunk['content'] for chunk in relevant_chunks]
                    document_context = "\n\n".join(context_texts)
            
            # Generate response based on available model
            if self.model and self.tokenizer:
                response_data = self._generate_with_dialogpt(message, document_context, temperature)
            elif self.chat_pipeline:
                response_data = self._generate_with_pipeline(message, document_context, temperature)
            else:
                response_data = self._generate_fallback_response(message, document_context)
            
            # Add context information
            response_data.update({
                "relevant_chunks": len(relevant_chunks),
                "document_context_used": len(document_context) > 0,
                "model_used": self.current_model_name,
                "document_info": {
                    "filename": self.current_document_metadata.get('filename', 'None'),
                    "total_chunks": len(self.current_document_chunks),
                    "file_type": self.current_document_metadata.get('file_type', 'unknown')
                }
            })
            
            # Update conversation history
            self._update_conversation_history(message, response_data['response'])
            
            return response_data
            
        except Exception as e:
            logging.error(f"Response generation error: {e}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Could you please try rephrasing your question?",
                "confidence": 0.3,
                "emotion": "apologetic",
                "model_used": "error_fallback",
                "error": str(e)
            }
    
    def _get_relevant_context(self, query: str, max_chunks: int = 3) -> List[Dict]:
        """Retrieve relevant document chunks using semantic search"""
        if not self.embedder or not self.current_document_chunks or not self.current_document_embeddings:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedder.encode([query])
            
            # Calculate similarities with all chunks
            similarities = []
            for i, chunk_embedding in enumerate(self.current_document_embeddings):
                similarity = np.dot(query_embedding[0], chunk_embedding) / (
                    np.linalg.norm(query_embedding[0]) * np.linalg.norm(chunk_embedding)
                )
                similarities.append((i, float(similarity)))
            
            # Sort by similarity and get top chunks
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            relevant_chunks = []
            for i, (chunk_idx, similarity) in enumerate(similarities[:max_chunks]):
                if similarity > 0.3:  # Only include reasonably relevant chunks
                    chunk_copy = self.current_document_chunks[chunk_idx].copy()
                    chunk_copy['similarity_score'] = similarity
                    chunk_copy['rank'] = i + 1
                    relevant_chunks.append(chunk_copy)
            
            return relevant_chunks
            
        except Exception as e:
            print(f"⚠️ Context retrieval failed: {e}")
            return []
    
    def _generate_with_dialogpt(self, message: str, document_context: str, temperature: float) -> Dict:
        """Generate response using DialoGPT model"""
        try:
            # Build conversation context
            context_parts = []
            
            # Add document context if available
            if document_context:
                context_parts.append(f"Based on the document: {document_context[:800]}")
            
            # Add recent conversation history
            for exchange in self.conversation_history[-3:]:
                context_parts.append(f"Human: {exchange['user']}")
                context_parts.append(f"Assistant: {exchange['assistant']}")
            
            # Add current message
            context_parts.append(f"Human: {message}")
            context_parts.append("Assistant:")
            
            # Encode input
            input_text = "\n".join(context_parts)
            input_ids = self.tokenizer.encode(
                input_text, 
                return_tensors='pt',
                truncation=True,
                max_length=self.max_context_length
            )
            
            # Generate response
            with torch.no_grad():
                output_ids = self.model.generate(
                    input_ids,
                    max_new_tokens=self.max_response_length,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    no_repeat_ngram_size=3,
                    top_p=0.9
                )
            
            # Decode response
            response = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
            
            # Extract only the new response part
            response = response.replace(input_text, "").strip()
            
            # Clean up response
            response = self._clean_response(response, message)
            
            if not response or len(response) < 5:
                return self._generate_fallback_response(message, document_context)
            
            return {
                "response": response,
                "confidence": 0.85,
                "emotion": self._detect_emotion(response),
                "generation_method": "dialogpt"
            }
            
        except Exception as e:
            print(f"⚠️ DialoGPT generation failed: {e}")
            return self._generate_fallback_response(message, document_context)
    
    def _generate_with_pipeline(self, message: str, document_context: str, temperature: float) -> Dict:
        """Generate response using Hugging Face pipeline"""
        try:
            # Build context
            context_parts = []
            
            if document_context:
                context_parts.append(f"Document context: {document_context[:600]}")
            
            # Add conversation history
            for exchange in self.conversation_history[-2:]:
                context_parts.append(f"User: {exchange['user']}")
                context_parts.append(f"Bot: {exchange['assistant']}")
            
            context_parts.append(f"User: {message}")
            context_parts.append("Bot:")
            
            input_text = "\n".join(context_parts)
            
            # Generate response
            result = self.chat_pipeline(
                input_text,
                max_length=len(input_text) + self.max_response_length,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.chat_pipeline.tokenizer.pad_token_id
            )
            
            # Extract response
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0]['generated_text']
                response = generated_text.replace(input_text, "").strip()
            else:
                response = str(result).strip()
            
            response = self._clean_response(response, message)
            
            if not response or len(response) < 5:
                return self._generate_fallback_response(message, document_context)
            
            return {
                "response": response,
                "confidence": 0.80,
                "emotion": self._detect_emotion(response),
                "generation_method": "pipeline"
            }
            
        except Exception as e:
            print(f"⚠️ Pipeline generation failed: {e}")
            return self._generate_fallback_response(message, document_context)
    
    def _clean_response(self, response: str, original_message: str) -> str:
        """Clean and improve generated response"""
        # Remove repetitive patterns
        response = re.sub(r'(.+?)\1+', r'\1', response)
        
        # Remove original message if repeated
        response = response.replace(original_message, "").strip()
        
        # Remove common artifacts
        artifacts = ['Human:', 'Assistant:', 'User:', 'Bot:', 'Context:', 'Document:']
        for artifact in artifacts:
            response = response.replace(artifact, "").strip()
        
        # Clean up whitespace
        response = re.sub(r'\s+', ' ', response).strip()
        
        # Ensure proper sentence ending
        if response and not response.endswith(('.', '!', '?')):
            response += "."
        
        # Handle very short responses
        if len(response) < 10:
            return ""
        
        # Limit response length
        if len(response) > 300:
            # Try to cut at sentence boundary
            sentences = response.split('.')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + ".") <= 300:
                    truncated += sentence + "."
                else:
                    break
            response = truncated if truncated else response[:300] + "..."
        
        return response
    
    def _generate_fallback_response(self, message: str, document_context: str) -> Dict:
        """Generate fallback response using pattern matching and context"""
        message_lower = message.lower()
        
        # Document-specific responses
        if document_context and any(word in message_lower for word in ['what', 'explain', 'tell', 'describe']):
            # Try to answer based on document context
            context_words = document_context.lower().split()
            
            if any(word in message_lower for word in ['summary', 'summarize', 'about']):
                response = f"Based on the document, here's what I found: {document_context[:200]}... Would you like me to elaborate on any specific part?"
            elif 'how' in message_lower:
                response = f"From the document, I can see information about your question. {document_context[:150]}... Let me know if you'd like more details on any aspect."
            else:
                # Extract relevant sentences from context
                sentences = document_context.split('.')[:3]
                response = f"According to the document: {'. '.join(sentences)}. What specific aspect would you like to explore further?"
        
        # General conversation patterns
        elif any(word in message_lower for word in ['hello', 'hi', 'hey']):
            doc_info = ""
            if self.current_document_metadata.get('filename'):
                doc_info = f" I've analyzed your document '{self.current_document_metadata['filename']}' and I'm ready to discuss it with you."
            response = f"Hello! I'm your AI assistant.{doc_info} How can I help you today?"
            
        elif any(word in message_lower for word in ['thank', 'thanks']):
            response = "You're welcome! I'm here to help you understand and work with your documents. Feel free to ask me anything else!"
            
        elif 'help' in message_lower:
            doc_context_info = ""
            if self.current_document_chunks:
                doc_context_info = f" I have access to your document '{self.current_document_metadata.get('filename', 'uploaded file')}' and can answer questions about it."
            response = f"I can help you in several ways:{doc_context_info} You can ask me to explain concepts, summarize sections, find specific information, or discuss the content. What would you like to explore?"
            
        elif any(word in message_lower for word in ['find', 'search', 'look for']):
            if document_context:
                response = "I can search through the document for you. Based on your question, here's what I found relevant: " + document_context[:200] + "... Would you like me to look for something more specific?"
            else:
                response = "I'd be happy to help you find information. Could you upload a document or be more specific about what you're looking for?"
                
        else:
            # Generic helpful response
            doc_help = ""
            if self.current_document_chunks:
                doc_help = f" I have your document '{self.current_document_metadata.get('filename')}' loaded and can help you understand, analyze, or discuss its contents."
            response = f"I understand you're asking about that topic.{doc_help} Could you provide more context or ask a specific question so I can give you a more helpful answer?"
        
        return {
            "response": response,
            "confidence": 0.70,
            "emotion": "helpful",
            "generation_method": "pattern_matching_with_context"
        }
    
    def _detect_emotion(self, text: str) -> str:
        """Detect emotion in generated text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['excited', 'amazing', 'excellent', 'fantastic', 'wonderful']):
            return "excited"
        elif any(word in text_lower for word in ['happy', 'glad', 'pleased', 'great', 'good']):
            return "happy"
        elif any(word in text_lower for word in ['sorry', 'apologize', 'unfortunately', 'problem']):
            return "apologetic"
        elif any(word in text_lower for word in ['interesting', 'curious', 'wonder', 'explore']):
            return "curious"
        elif any(word in text_lower for word in ['help', 'assist', 'support', 'guide']):
            return "helpful"
        elif "?" in text:
            return "inquisitive"
        else:
            return "neutral"
    
    def _update_conversation_history(self, user_message: str, assistant_response: str):
        """Update conversation history"""
        self.conversation_history.append({
            "user": user_message,
            "assistant": assistant_response
        })
        
        # Keep only recent history to manage memory
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-8:]
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to a different chat model"""
        if model_name in self.chat_models:
            try:
                self._load_chat_model(model_name)
                return True
            except Exception as e:
                print(f"⚠️ Failed to switch to {model_name}: {e}")
                return False
        return False
    
    def get_available_models(self) -> Dict[str, str]:
        """Get available chat models"""
        return self.chat_models.copy()
    
    def get_conversation_summary(self) -> Dict:
        """Get summary of current conversation"""
        return {
            "total_exchanges": len(self.conversation_history),
            "current_model": self.current_model_name,
            "document_loaded": len(self.current_document_chunks) > 0,
            "document_info": self.current_document_metadata,
            "recent_topics": self._extract_recent_topics()
        }
    
    def _extract_recent_topics(self) -> List[str]:
        """Extract topics from recent conversation"""
        if not self.conversation_history:
            return []
        
        recent_messages = []
        for exchange in self.conversation_history[-5:]:
            recent_messages.extend([exchange["user"], exchange["assistant"]])
        
        combined_text = " ".join(recent_messages).lower()
        
        # Simple keyword extraction
        topic_keywords = {
            'document analysis': ['analyze', 'analysis', 'document', 'content', 'text'],
            'summarization': ['summary', 'summarize', 'main points', 'overview'],
            'explanation': ['explain', 'clarify', 'understand', 'meaning'],
            'search': ['find', 'search', 'look', 'locate'],
            'comparison': ['compare', 'difference', 'similar', 'contrast']
        }
        
        detected_topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                detected_topics.append(topic)
        
        return detected_topics[:3]
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def clear_document_context(self):
        """Clear loaded document context"""
        self.current_document_chunks = []
        self.current_document_embeddings = []
        self.current_document_metadata = {}
        self.conversation_history = []