from transformers import pipeline
import re
from typing import List, Dict
import logging

class ChatModel:
    """Conversational AI using Hugging Face models"""
    
    def __init__(self):
        self.pipeline = None
        self.model_name = "microsoft/DialoGPT-medium"
        self.device = -1  # CPU by default
        self._load_model()
    
    def _load_model(self):
        """Load conversational AI model"""
        try:
            print("📥 Loading conversational AI model...")
            
            # Use a more reliable conversational model
            self.pipeline = pipeline(
                "conversational",
                model="facebook/blenderbot-400M-distill",
                device=self.device
            )
            
            print("✅ Chat model loaded successfully!")
            
        except Exception as e:
            print(f"⚠️ Error loading chat model: {e}")
            print("🔄 Using fallback conversation approach...")
            self.pipeline = None
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.pipeline is not None
    
    def generate_response(self, message: str, context: str = "", language: str = "en", history: List[dict] = []) -> Dict:
        """Generate conversational response"""
        try:
            if self.pipeline is None:
                return self._fallback_response(message, context, language)
            
            # Prepare conversation context
            conversation_context = self._build_context(message, context, history)
            
            # Generate response
            response = self.pipeline(conversation_context)
            
            # Extract response text
            if isinstance(response, list) and len(response) > 0:
                response_text = response[0].get('generated_text', '').strip()
            else:
                response_text = str(response).strip()
            
            # Clean and enhance response
            cleaned_response = self._clean_response(response_text, message)
            
            # Detect emotion based on response content
            emotion = self._detect_emotion(cleaned_response)
            
            return {
                "response": cleaned_response,
                "emotion": emotion,
                "confidence": 0.85,
                "model": "huggingface_blenderbot"
            }
            
        except Exception as e:
            print(f"❌ Chat generation error: {e}")
            return self._fallback_response(message, context, language)
    
    def _build_context(self, message: str, context: str, history: List[dict]) -> str:
        """Build conversation context"""
        context_parts = []
        
        # Add document context if available
        if context:
            context_parts.append(f"Context: {context[:500]}")
        
        # Add recent conversation history
        if history:
            recent_history = history[-3:]  # Last 3 exchanges
            for exchange in recent_history:
                if 'user' in exchange:
                    context_parts.append(f"User: {exchange['user']}")
                if 'assistant' in exchange:
                    context_parts.append(f"Assistant: {exchange['assistant']}")
        
        # Add current message
        context_parts.append(f"User: {message}")
        context_parts.append("Assistant:")
        
        return "\n".join(context_parts)
    
    def _clean_response(self, response: str, original_message: str) -> str:
        """Clean and improve the generated response"""
        # Remove any repetitive patterns
        response = re.sub(r'(.+?)\1+', r'\1', response)
        
        # Remove user message if it got repeated
        response = response.replace(original_message, "").strip()
        
        # Clean up common issues
        response = re.sub(r'\s+', ' ', response)
        response = response.strip()
        
        # Ensure response ends properly
        if response and not response.endswith(('.', '!', '?')):
            response += "."
        
        # Handle empty responses
        if not response or len(response) < 10:
            return self._get_default_response(original_message)
        
        return response
    
    def _detect_emotion(self, text: str) -> str:
        """Simple emotion detection based on keywords"""
        positive_words = ['great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'good', 'nice', 'love']
        negative_words = ['sorry', 'unfortunately', 'problem', 'error', 'difficult', 'hard', 'bad']
        excited_words = ['exciting', 'incredible', 'awesome', 'brilliant', 'outstanding']
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in excited_words):
            return "excited"
        elif any(word in text_lower for word in positive_words):
            return "happy"
        elif any(word in text_lower for word in negative_words):
            return "concerned"
        elif "?" in text:
            return "curious"
        else:
            return "neutral"
    
    def _fallback_response(self, message: str, context: str, language: str) -> Dict:
        """Fallback response when model is not available"""
        
        # Simple pattern-based responses
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            response = "Hello! I'm your AI educational assistant. How can I help you learn today?"
            emotion = "friendly"
        elif any(word in message_lower for word in ['thank', 'thanks']):
            response = "You're welcome! I'm here to help you with your studies anytime."
            emotion = "happy"
        elif 'summary' in message_lower or 'summarize' in message_lower:
            response = "I can help you create summaries of your documents. Please upload a document and I'll analyze it for you!"
            emotion = "helpful"
        elif any(word in message_lower for word in ['help', 'how', 'what', 'explain']):
            if context:
                response = f"Based on your document, I can see it discusses {context[:100]}... What specific aspect would you like me to explain further?"
            else:
                response = "I'm here to help! You can ask me to summarize documents, create quizzes, or explain concepts. What would you like to explore?"
            emotion = "thoughtful"
        elif 'quiz' in message_lower:
            response = "I can generate quizzes based on your documents to help test your knowledge. Upload some content and I'll create questions for you!"
            emotion = "encouraging"
        else:
            if context:
                # Try to give a contextual response
                response = f"That's an interesting question about your document. Based on the content, I can tell you that it covers topics related to your uploaded material. Could you be more specific about what you'd like to know?"
            else:
                response = "I understand you're asking about that topic. Could you provide more context or upload a relevant document so I can give you a more detailed answer?"
            emotion = "curious"
        
        return {
            "response": response,
            "emotion": emotion,
            "confidence": 0.75,
            "model": "fallback_pattern_matching"
        }
    
    def _get_default_response(self, message: str) -> str:
        """Get a default response for edge cases"""
        defaults = [
            "That's an interesting point. Could you tell me more about what you'd like to explore?",
            "I see what you're asking about. Let me help you understand this better.",
            "That's a good question! Based on your uploaded documents, I can provide more specific information.",
            "I'm here to help you learn. What specific aspect would you like me to focus on?"
        ]
        
        # Simple hash-based selection for consistency
        index = len(message) % len(defaults)
        return defaults[index]
    
    def get_model_info(self) -> Dict:
        """Get information about the chat model"""
        return {
            "model_name": self.model_name if self.pipeline else "Pattern-based fallback",
            "loaded": self.is_loaded(),
            "device": "CPU" if self.device == -1 else "GPU",
            "capabilities": [
                "Conversational AI",
                "Context-aware responses", 
                "Multi-turn conversations",
                "Emotion detection",
                "Educational focus"
            ]
        }