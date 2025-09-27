# 🤖 GENAVATOR1 - AI Educational Avatar

> **Advanced AI-powered educational system with PyMuPDF document processing, 3D talking avatar, and intelligent conversational capabilities**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PyMuPDF](https://img.shields.io/badge/PyMuPDF-40826D?style=for-the-badge)](https://pymupdf.readthedocs.io/)
[![Three.js](https://img.shields.io/badge/Three.js-000000?style=for-the-badge&logo=three.js)](https://threejs.org/)
[![Node.js](https://img.shields.io/badge/Node.js-43853D?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org/)

## 🌟 Features

### 📄 Document Processing
- **PyMuPDF Integration**: High-quality PDF text extraction with structure preservation
- **Multi-format Support**: PDF, DOCX, TXT, MD, JSON, CSV files
- **Semantic Chunking**: Intelligent content segmentation for better AI understanding
- **Content Analysis**: Keyword extraction, readability scoring, and topic identification

### 🧠 AI Capabilities
- **Document-Aware Chat**: AI responses based on uploaded document content
- **Context Retrieval**: Semantic search through document chunks
- **Multiple Summarization**: General, academic, and bullet-point summaries
- **Conversation Memory**: Maintains context across chat sessions

### 🎭 3D Avatar Features
- **Realistic 3D Avatar**: Talking head with lip-sync capabilities
- **Multiple Moods**: Teacher, friendly, energetic, and calm modes
- **Voice Integration**: Speech-to-text input and text-to-speech output
- **Multilingual Support**: English, Spanish, French, German, Chinese, Japanese, Korean, Arabic

### 🎮 Gamification
- **XP System**: Earn experience points for learning activities
- **Achievement System**: Unlock badges for various milestones
- **Progress Tracking**: Monitor learning progress and statistics
- **Study Games**: Interactive learning games and challenges

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Frontend      │    │   Node.js        │    │   GENAVATOR1        │
│   (Port 3000)   │◄──►│   Backend        │    │   AI Backend        │
│                 │    │   (Port 3001)    │    │   (Port 8000)       │
│ • 3D Avatar     │    │                  │    │                     │
│ • Chat UI       │    │ • Database       │    │ • PyMuPDF           │
│ • File Upload   │    │ • TTS/STT        │    │ • Document AI       │
│ • Voice Input   │    │ • Gamification   │    │ • Chat AI           │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- Modern web browser with WebGL support

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/genavator1.git
   cd genavator1
   ```

2. **Set up Python AI Backend**
   ```bash
   cd ai-backend
   pip install -r requirements.txt
   python genavator_main.py
   ```

3. **Set up Node.js Backend**
   ```bash
   cd backend
   npm install
   node server.js
   ```

4. **Start Frontend Server**
   ```bash
   python -m http.server 3000
   ```

5. **Open your browser**
   ```
   http://localhost:3000/ai-educational-avatar.html
   ```

## 📋 Usage

1. **Upload Documents**: Drag and drop PDF, Word, or text files
2. **Ask Questions**: Chat with the AI about your uploaded content
3. **Use Voice**: Click the microphone for voice input
4. **Study Modes**: Choose from summarize, quiz, explain, or flashcard modes
5. **Language Support**: Switch between 8+ supported languages

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework for AI services
- **PyMuPDF**: High-quality PDF processing and text extraction
- **Node.js**: Traditional backend services and database management
- **SQLite**: Lightweight database for user progress and documents

### Frontend
- **Three.js**: 3D graphics and avatar rendering
- **WebGL**: Hardware-accelerated graphics
- **Web Speech API**: Voice recognition and synthesis
- **Modern ES6+**: Clean, modular JavaScript code

### AI & ML
- **Lightweight AI Models**: Efficient document processing and chat
- **Semantic Chunking**: Intelligent text segmentation
- **Context Retrieval**: Smart content search and matching

## 📁 Project Structure

```
GENAVATOR1/
├── ai-backend/                 # FastAPI AI Backend
│   ├── genavator_main.py      # Main FastAPI application
│   ├── lightweight_chat_model.py
│   ├── lightweight_document_processor.py
│   ├── lightweight_summarizer.py
│   └── requirements.txt
├── backend/                   # Node.js Backend
│   ├── server.js
│   ├── package.json
│   └── database/
├── modules/                   # 3D Avatar modules
│   ├── talkinghead.mjs
│   ├── lipsync-*.mjs
│   └── dynamicbones.mjs
├── avatars/                   # 3D Avatar models
├── audio/                     # Audio files
├── ai-educational-avatar.html # Main frontend
└── README.md
```

## 🎯 Key Features Demo

### Document Upload & Processing
```javascript
// Upload with PyMuPDF processing
await fetch('http://localhost:8000/api/v1/upload', {
  method: 'POST',
  body: formData
});
```

### AI Chat with Document Context
```javascript
// Document-aware conversation
const response = await fetch('http://localhost:8000/api/v1/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "What are the key points?",
    context: documentContext
  })
});
```

## 🔧 Configuration

### Environment Variables
```bash
# AI Backend Configuration
GENAVATOR_HOST=0.0.0.0
GENAVATOR_PORT=8000
GENAVATOR_DEBUG=false

# Node.js Backend
NODE_ENV=development
PORT=3001
```

### Supported File Formats
- **PDF**: High-quality extraction with PyMuPDF
- **DOCX**: Microsoft Word documents
- **TXT**: Plain text files
- **MD**: Markdown documents
- **JSON**: Structured data files
- **CSV**: Comma-separated values

## 📊 Performance

- **Document Processing**: < 2 seconds for typical PDFs
- **AI Response Time**: < 1 second for chat queries
- **Memory Usage**: Lightweight, < 500MB total
- **Supported File Size**: Up to 50MB documents

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PyMuPDF**: Excellent PDF processing library
- **Three.js**: Powerful 3D graphics framework
- **FastAPI**: Modern Python web framework
- **TalkingHead**: 3D avatar animation system

## 🔗 Links

- [Demo Video](#) (Coming soon)
- [Documentation](#) (In progress)
- [API Reference](#) (Available at `/docs` when running)

---

**Built with ❤️ for enhanced learning experiences**

*GENAVATOR1 - Where AI meets Education*