# FastAPI + Hugging Face AI Backend

This is a FastAPI microservice that provides local AI capabilities using Hugging Face transformers, designed to integrate with the existing Node.js educational avatar system.

## Features

### 🤖 Local AI Models
- **Summarization**: BART, T5, and Pegasus models for document summarization
- **Chat**: Conversational AI using BlenderBot and DialoGPT
- **Multiple Summary Types**: Academic summaries, bullet points, key insights
- **Offline Processing**: No external API calls required

### 📄 Document Processing
- **Multi-format Support**: PDF, DOCX, TXT, MD, XLSX, PPTX, JSON, CSV, RTF
- **Content Analysis**: Word count, reading time, keyword extraction
- **Language Detection**: Basic language identification
- **Content Type Detection**: Academic, technical, business document classification

### 🔗 Integration Ready
- **CORS Enabled**: Ready for frontend integration
- **RESTful API**: Standard HTTP endpoints
- **Async Processing**: Non-blocking document processing
- **Batch Operations**: Multiple document analysis

## Quick Start

### 1. Install Dependencies
```bash
cd ai-backend
pip install -r requirements.txt
```

### 2. Download NLTK Data
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

### 3. Start the Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **Main API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API Endpoints

### 📤 Document Upload & Processing
```
POST /upload
- Upload and process documents
- Returns: Content, analysis, and metadata
```

### 📝 Summarization
```
POST /summarize
- Generate summaries from text or uploaded documents
- Supports: academic, bullets, insights formats
- Models: BART, T5, Pegasus
```

### 💬 Chat
```
POST /chat
- Conversational AI with context awareness
- Supports conversation history
- Emotion detection included
```

### 📊 Batch Analysis
```
POST /analyze/batch
- Process multiple documents simultaneously
- Generate comparative analysis
- Bulk summarization
```

### ℹ️ System Information
```
GET /health - Health check
GET /models - Available models info
GET /formats - Supported file formats
```

## Model Configuration

### Default Models
- **Summarization**: `facebook/bart-large-cnn`
- **Chat**: `facebook/blenderbot-400M-distill`
- **Fallback**: Pattern-based responses

### Customization
Edit model names in:
- `summarizer.py` - Line 15-18
- `models.py` - Line 9

## Integration with Node.js Frontend

### Frontend API Calls
```javascript
// Summarize document
const response = await fetch('http://localhost:8000/summarize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        text: documentContent,
        summary_type: 'academic',
        model: 'bart'
    })
});

// Chat with AI
const chatResponse = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: userMessage,
        context: documentContext,
        history: conversationHistory
    })
});
```

### Dual Backend Architecture
- **Node.js (Port 3001)**: Existing features, database, OpenAI integration
- **FastAPI (Port 8000)**: Local AI models, document processing
- **Frontend (Port 3000)**: Unified interface using both backends

## File Structure

```
ai-backend/
├── main.py                 # FastAPI application and routes
├── summarizer.py          # Hugging Face summarization models
├── models.py              # Conversational AI models
├── document_processor.py  # Document parsing and analysis
├── requirements.txt       # Python dependencies
├── README.md             # This documentation
└── temp_uploads/         # Temporary file storage (created automatically)
```

## Performance & Resource Usage

### CPU Mode (Default)
- **Memory**: ~2-4GB RAM
- **Speed**: 5-15 seconds per summary
- **Suitable**: Development, light usage

### GPU Mode (Optional)
- **Requirements**: NVIDIA GPU with CUDA
- **Memory**: ~6-8GB VRAM
- **Speed**: 1-3 seconds per summary
- **Setup**: Uncomment GPU packages in requirements.txt

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Install missing packages
pip install transformers torch nltk

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

**Memory Issues**
```python
# Use smaller models in summarizer.py
MODEL_BART = "facebook/bart-base"  # Instead of bart-large-cnn
```

**Slow Performance**
- First model load takes longer (downloading weights)
- Subsequent requests are much faster
- Consider using GPU for production

### Health Check
```bash
curl http://localhost:8000/health
```

## Development

### Adding New Models
1. Edit `summarizer.py` or `models.py`
2. Add model configuration
3. Update requirements.txt if needed
4. Test with `/models` endpoint

### Custom Document Formats
1. Add parser to `document_processor.py`
2. Update `supported_formats` list
3. Add extraction method

## Production Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.9-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
```bash
export TRANSFORMERS_CACHE=/path/to/model/cache
export TOKENIZERS_PARALLELISM=false  # Avoid warnings
```

## License

Same license as the main project (see LICENSE file).

## Integration Examples

See the main project documentation for complete examples of using this FastAPI backend with the Node.js educational avatar system.