"""
Test script for the enhanced AI backend
Run this after installing dependencies to verify everything works
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        # Test FastAPI
        import fastapi
        print("✅ FastAPI imported successfully")
        
        # Test PyMuPDF
        import fitz
        print("✅ PyMuPDF (fitz) imported successfully")
        
        # Test sentence transformers
        from sentence_transformers import SentenceTransformer
        print("✅ Sentence Transformers imported successfully")
        
        # Test transformers
        from transformers import pipeline
        print("✅ Hugging Face Transformers imported successfully")
        
        # Test torch
        import torch
        device = "GPU" if torch.cuda.is_available() else "CPU"
        print(f"✅ PyTorch imported successfully (Device: {device})")
        
        # Test pandas
        import pandas as pd
        print("✅ Pandas imported successfully")
        
        # Test NLTK
        import nltk
        print("✅ NLTK imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_document_processor():
    """Test advanced document processor"""
    print("\n📄 Testing Advanced Document Processor...")
    
    try:
        from advanced_document_processor import AdvancedDocumentProcessor
        processor = AdvancedDocumentProcessor()
        print("✅ Advanced Document Processor initialized")
        
        # Test supported formats
        formats = processor.get_supported_formats()
        print(f"✅ Supported formats: {', '.join(formats)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Document processor test failed: {e}")
        return False

def test_chat_model():
    """Test document-aware chat model"""
    print("\n💬 Testing Document-Aware Chat Model...")
    
    try:
        from document_chat_model import DocumentAwareChatModel
        chat_model = DocumentAwareChatModel()
        print("✅ Document-Aware Chat Model initialized")
        
        # Test basic response
        response = chat_model.generate_response("Hello, how are you?", use_document_context=False)
        print(f"✅ Generated response: {response['response'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Chat model test failed: {e}")
        return False

def test_summarizer():
    """Test document summarizer"""
    print("\n📝 Testing Document Summarizer...")
    
    try:
        from summarizer import DocumentSummarizer
        summarizer = DocumentSummarizer()
        print("✅ Document Summarizer initialized")
        
        # Test summarization
        test_text = "This is a test document. It contains multiple sentences for testing purposes. The summarizer should be able to process this text and create a shorter version."
        summary = summarizer.summarize(test_text, max_length=30)
        print(f"✅ Generated summary: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Summarizer test failed: {e}")
        return False

def test_sentence_transformer():
    """Test sentence transformer for embeddings"""
    print("\n🔍 Testing Sentence Transformer...")
    
    try:
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Sentence Transformer loaded")
        
        # Test embedding generation
        test_sentences = ["This is a test sentence.", "Another sentence for testing."]
        embeddings = embedder.encode(test_sentences)
        print(f"✅ Generated embeddings shape: {embeddings.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sentence Transformer test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 GENAVATOR1 Enhanced AI Backend Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_document_processor,
        test_summarizer,
        test_sentence_transformer,
        test_chat_model
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your enhanced AI backend is ready to use!")
        print("\n🚀 Next steps:")
        print("   1. Run START_ALL_SERVERS.bat")
        print("   2. Upload a document at http://localhost:8000/docs")
        print("   3. Chat with your document!")
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("❌ Some components may not work properly")
        print("💡 Try running INSTALL_AI_BACKEND.bat again")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()