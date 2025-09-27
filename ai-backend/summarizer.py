from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from typing import List, Dict
import re
import nltk
from nltk.tokenize import sent_tokenize
import logging

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
except:
    pass

class DocumentSummarizer:
    """Advanced document summarization using Hugging Face transformers"""
    
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.pipelines = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔧 Using device: {self.device}")
        
        self._load_models()
    
    def _load_models(self):
        """Load multiple summarization models for different use cases"""
        try:
            # BART model - excellent for general summarization
            print("📥 Loading BART summarization model...")
            self.pipelines['bart'] = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                tokenizer="facebook/bart-large-cnn",
                device=0 if self.device == "cuda" else -1
            )
            
            # T5 model - great for abstractive summaries
            print("📥 Loading T5 summarization model...")
            self.pipelines['t5'] = pipeline(
                "summarization",
                model="t5-small",
                tokenizer="t5-small",
                device=0 if self.device == "cuda" else -1
            )
            
            # Pegasus - specialized for news/document summarization
            print("📥 Loading Pegasus model...")
            try:
                self.pipelines['pegasus'] = pipeline(
                    "summarization",
                    model="google/pegasus-xsum",
                    tokenizer="google/pegasus-xsum",
                    device=0 if self.device == "cuda" else -1
                )
            except Exception as e:
                print(f"⚠️ Pegasus model not available: {e}")
                self.pipelines['pegasus'] = None
            
            print("✅ Summarization models loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            # Fallback to basic pipeline
            self.pipelines['bart'] = pipeline("summarization")
    
    def is_loaded(self) -> bool:
        """Check if models are loaded"""
        return len(self.pipelines) > 0 and any(p is not None for p in self.pipelines.values())
    
    def summarize(self, text: str, max_length: int = 150, min_length: int = 50, model: str = "bart") -> str:
        """Generate summary using specified model"""
        try:
            # Clean and prepare text
            cleaned_text = self._preprocess_text(text)
            
            # Choose model
            pipeline_model = self.pipelines.get(model, self.pipelines['bart'])
            if pipeline_model is None:
                pipeline_model = self.pipelines['bart']
            
            # Generate summary
            if model == "t5":
                # T5 requires specific prefix
                input_text = f"summarize: {cleaned_text}"
            else:
                input_text = cleaned_text
            
            # Handle long texts by chunking
            if len(input_text.split()) > 1000:
                return self._summarize_long_text(input_text, max_length, min_length, pipeline_model)
            
            summary = pipeline_model(
                input_text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                early_stopping=True
            )
            
            return summary[0]['summary_text'].strip()
            
        except Exception as e:
            print(f"❌ Summarization error: {e}")
            return self._fallback_summary(text, max_length)
    
    def academic_summary(self, text: str, max_length: int = 200) -> str:
        """Generate academic-style summary with key findings"""
        try:
            # Use BART for academic summaries
            pipeline_model = self.pipelines.get('bart')
            
            # Academic-focused preprocessing
            cleaned_text = self._preprocess_academic_text(text)
            
            summary = pipeline_model(
                cleaned_text,
                max_length=max_length,
                min_length=max_length // 3,
                do_sample=True,
                temperature=0.7,
                early_stopping=True
            )
            
            return f"Academic Summary: {summary[0]['summary_text'].strip()}"
            
        except Exception as e:
            return self.summarize(text, max_length)
    
    def bullet_point_summary(self, text: str) -> str:
        """Generate bullet-point style summary"""
        try:
            # Get regular summary first
            summary = self.summarize(text, max_length=200, min_length=100)
            
            # Convert to bullet points
            sentences = sent_tokenize(summary)
            bullet_points = []
            
            for sentence in sentences:
                if len(sentence.strip()) > 20:  # Filter out very short sentences
                    bullet_points.append(f"• {sentence.strip()}")
            
            return "\n".join(bullet_points[:5])  # Limit to 5 points
            
        except Exception as e:
            return f"• {self.summarize(text, max_length=100)}"
    
    def extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text using NLP techniques"""
        try:
            # Get sentences
            sentences = sent_tokenize(text)
            
            # Simple keyword-based extraction
            keywords = ['important', 'significant', 'key', 'main', 'primary', 'essential', 'crucial']
            key_sentences = []
            
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in keywords):
                    key_sentences.append(sentence.strip())
            
            # If no keyword-based sentences, use first few sentences
            if not key_sentences:
                key_sentences = sentences[:3]
            
            return key_sentences[:5]  # Return max 5 key points
            
        except Exception as e:
            return [self.summarize(text, max_length=50)]
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for summarization"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.,;:!?()-]', '', text)
        
        # Limit length to avoid model constraints
        words = text.split()
        if len(words) > 1000:
            text = ' '.join(words[:1000])
        
        return text.strip()
    
    def _preprocess_academic_text(self, text: str) -> str:
        """Preprocess text with focus on academic content"""
        # Standard preprocessing
        text = self._preprocess_text(text)
        
        # Look for academic indicators
        academic_indicators = ['research', 'study', 'analysis', 'findings', 'conclusion', 'methodology']
        
        # Split into sentences and prioritize academic content
        sentences = sent_tokenize(text)
        academic_sentences = []
        other_sentences = []
        
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in academic_indicators):
                academic_sentences.append(sentence)
            else:
                other_sentences.append(sentence)
        
        # Prioritize academic sentences
        prioritized_text = ' '.join(academic_sentences + other_sentences[:5])
        
        return prioritized_text[:2000]  # Limit for model
    
    def _summarize_long_text(self, text: str, max_length: int, min_length: int, pipeline_model) -> str:
        """Handle long texts by chunking and combining summaries"""
        words = text.split()
        chunk_size = 800
        chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
        
        chunk_summaries = []
        for chunk in chunks[:3]:  # Limit to first 3 chunks
            try:
                summary = pipeline_model(
                    chunk,
                    max_length=max_length // len(chunks) + 50,
                    min_length=min_length // len(chunks),
                    do_sample=False
                )
                chunk_summaries.append(summary[0]['summary_text'])
            except:
                continue
        
        # Combine chunk summaries
        combined_summary = ' '.join(chunk_summaries)
        
        # Final summarization of combined summaries
        if len(combined_summary.split()) > max_length:
            final_summary = pipeline_model(
                combined_summary,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            return final_summary[0]['summary_text']
        
        return combined_summary
    
    def _fallback_summary(self, text: str, max_length: int) -> str:
        """Simple fallback summarization"""
        sentences = sent_tokenize(text)
        
        # Take first few sentences up to max_length words
        summary_sentences = []
        word_count = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            if word_count + sentence_words <= max_length:
                summary_sentences.append(sentence)
                word_count += sentence_words
            else:
                break
        
        if not summary_sentences:
            words = text.split()[:max_length]
            return ' '.join(words) + "..."
        
        return ' '.join(summary_sentences)
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        return {
            "loaded_models": list(self.pipelines.keys()),
            "device": self.device,
            "available": self.is_loaded(),
            "model_details": {
                "bart": "Facebook BART-Large-CNN - General summarization",
                "t5": "Google T5-Small - Abstractive summarization",
                "pegasus": "Google Pegasus-XSUM - News/Document summarization"
            }
        }