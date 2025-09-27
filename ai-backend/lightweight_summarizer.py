from typing import Dict, List, Optional
import re
from collections import Counter

class LightweightSummarizer:
    """Lightweight text summarizer without heavy ML dependencies"""
    
    def __init__(self):
        self.max_summary_length = 500
        self.min_summary_length = 50
        print("✅ Lightweight summarizer initialized!")
    
    def summarize_text(self, text: str, max_length: int = None, min_length: int = None, 
                      summary_type: str = "general") -> Dict:
        """Generate summary using extractive methods"""
        try:
            if max_length is None:
                max_length = self.max_summary_length
            if min_length is None:
                min_length = self.min_summary_length
            
            if len(text) < min_length:
                return {
                    "summary": text,
                    "method": "original_text",
                    "length": len(text),
                    "confidence": 1.0
                }
            
            if summary_type == "bullet_points":
                summary = self._create_bullet_summary(text, max_length)
                method = "bullet_extraction"
            elif summary_type == "academic":
                summary = self._create_academic_summary(text, max_length)
                method = "academic_extraction"
            else:
                summary = self._create_general_summary(text, max_length)
                method = "extractive_general"
            
            return {
                "summary": summary,
                "method": method,
                "length": len(summary),
                "original_length": len(text),
                "compression_ratio": len(summary) / len(text),
                "confidence": 0.8
            }
            
        except Exception as e:
            return {
                "summary": "Error generating summary.",
                "method": "error",
                "error": str(e),
                "confidence": 0.0
            }
    
    def _create_general_summary(self, text: str, max_length: int) -> str:
        """Create general extractive summary"""
        sentences = self._split_sentences(text)
        
        if len(sentences) <= 3:
            return text
        
        # Score sentences based on various factors
        scored_sentences = []
        
        # Get word frequencies for scoring
        words = re.findall(r'\\b\\w+\\b', text.lower())
        word_freq = Counter(words)
        
        for i, sentence in enumerate(sentences):
            score = self._score_sentence(sentence, word_freq, i, len(sentences))
            scored_sentences.append((score, i, sentence))
        
        # Sort by score and select top sentences
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        
        # Select sentences that fit within max_length
        selected_sentences = []
        current_length = 0
        
        for score, original_index, sentence in scored_sentences:
            if current_length + len(sentence) <= max_length:
                selected_sentences.append((original_index, sentence))
                current_length += len(sentence)
        
        # Sort selected sentences by original order
        selected_sentences.sort(key=lambda x: x[0])
        summary = ' '.join([sentence for _, sentence in selected_sentences])
        
        return summary.strip()
    
    def _create_bullet_summary(self, text: str, max_length: int) -> str:
        """Create bullet point summary"""
        sentences = self._split_sentences(text)
        
        # Get key sentences
        key_sentences = sentences[:5] if len(sentences) > 5 else sentences
        
        # Convert to bullet points
        bullets = []
        current_length = 0
        
        for sentence in key_sentences:
            bullet_point = f"• {sentence.strip()}"
            if current_length + len(bullet_point) <= max_length:
                bullets.append(bullet_point)
                current_length += len(bullet_point) + 1  # +1 for newline
            else:
                break
        
        return '\\n'.join(bullets)
    
    def _create_academic_summary(self, text: str, max_length: int) -> str:
        """Create academic-style summary with key findings"""
        sentences = self._split_sentences(text)
        
        # Look for academic indicators
        academic_indicators = [
            'research', 'study', 'analysis', 'findings', 'conclusion',
            'methodology', 'results', 'data', 'evidence', 'investigation'
        ]
        
        # Score sentences based on academic relevance
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0
            sentence_lower = sentence.lower()
            
            # Higher score for sentences with academic terms
            for indicator in academic_indicators:
                if indicator in sentence_lower:
                    score += 1
            
            # Position-based scoring (intro and conclusion are important)
            if i < len(sentences) * 0.2:  # First 20%
                score += 2
            elif i > len(sentences) * 0.8:  # Last 20%
                score += 2
            
            scored_sentences.append((score, i, sentence))
        
        # Sort and select
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        
        selected_sentences = []
        current_length = 0
        
        for score, original_index, sentence in scored_sentences:
            if current_length + len(sentence) <= max_length and len(selected_sentences) < 4:
                selected_sentences.append((original_index, sentence))
                current_length += len(sentence)
        
        # Sort by original order
        selected_sentences.sort(key=lambda x: x[0])
        summary = ' '.join([sentence for _, sentence in selected_sentences])
        
        return summary.strip()
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        return sentences
    
    def _score_sentence(self, sentence: str, word_freq: Counter, position: int, total_sentences: int) -> float:
        """Score a sentence based on various factors"""
        score = 0.0
        
        # Word frequency score
        words = re.findall(r'\\b\\w+\\b', sentence.lower())
        for word in words:
            score += word_freq.get(word, 0)
        
        # Length penalty (too short or too long sentences get lower scores)
        length = len(sentence)
        if 50 <= length <= 200:
            score += 1
        elif length < 20:
            score -= 1
        
        # Position score (first and last sentences are often important)
        if position < total_sentences * 0.2:  # First 20%
            score += 2
        elif position > total_sentences * 0.8:  # Last 20%
            score += 1
        
        # Keyword indicators
        important_words = ['important', 'key', 'main', 'primary', 'significant', 
                          'conclusion', 'result', 'finding', 'however', 'therefore']
        sentence_lower = sentence.lower()
        for word in important_words:
            if word in sentence_lower:
                score += 1
        
        return score
    
    def get_model_info(self) -> Dict:
        """Get summarizer model information"""
        return {
            "name": "lightweight-extractive-summarizer",
            "methods": ["general", "academic", "bullet_points"],
            "max_length": self.max_summary_length,
            "min_length": self.min_summary_length,
            "type": "extractive",
            "status": "ready"
        }