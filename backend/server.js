const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs-extra');
require('dotenv').config();

// Import services
const DatabaseService = require('./services/DatabaseService');
const DocumentProcessor = require('./services/DocumentProcessor');
const AIService = require('./services/AIService');
const TTSService = require('./services/TTSService');
const UserService = require('./services/UserService');
const GamificationService = require('./services/GamificationService');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true
}));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Create necessary directories
const dirs = ['./uploads', './database', './temp', './audio'];
dirs.forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, './uploads/');
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({
  storage: storage,
  limits: {
    fileSize: parseInt(process.env.MAX_FILE_SIZE) || 10 * 1024 * 1024 // 10MB default
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];
    
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type. Supported: PDF, DOCX, TXT, PPTX, XLSX'), false);
    }
  }
});

// Initialize services
let dbService, docProcessor, aiService, ttsService, userService, gamificationService;

async function initializeServices() {
  try {
    console.log('🚀 Initializing services...');
    
    dbService = new DatabaseService();
    await dbService.initialize();
    
    docProcessor = new DocumentProcessor();
    aiService = new AIService();
    ttsService = new TTSService();
    userService = new UserService(dbService);
    gamificationService = new GamificationService(dbService);
    
    console.log('✅ All services initialized successfully');
  } catch (error) {
    console.error('❌ Error initializing services:', error);
    process.exit(1);
  }
}

// Routes

// Health check
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// User routes
app.post('/api/user/create', async (req, res) => {
  try {
    const { username, email } = req.body;
    const user = await userService.createUser(username, email);
    res.json({ success: true, user });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
});

app.get('/api/user/:userId', async (req, res) => {
  try {
    const user = await userService.getUser(req.params.userId);
    res.json({ success: true, user });
  } catch (error) {
    res.status(404).json({ success: false, error: error.message });
  }
});

// Document upload and processing
app.post('/api/documents/upload', upload.single('document'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, error: 'No file uploaded' });
    }

    const userId = req.body.userId || 'anonymous';
    console.log(`📤 Processing upload: ${req.file.originalname}`);

    // Extract text from document
    const extractedText = await docProcessor.extractText(req.file.path, req.file.mimetype);
    
    // Save document to database
    const document = await dbService.saveDocument({
      userId,
      filename: req.file.originalname,
      filePath: req.file.path,
      fileType: req.file.mimetype,
      fileSize: req.file.size,
      extractedText
    });

    // Process with AI asynchronously
    processDocumentWithAI(document.id, extractedText, userId);

    res.json({
      success: true,
      document: {
        id: document.id,
        filename: req.file.originalname,
        fileType: req.file.mimetype,
        fileSize: req.file.size,
        uploadedAt: document.created_at,
        processed: false
      }
    });

  } catch (error) {
    console.error('❌ Upload error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Async document processing with AI
async function processDocumentWithAI(documentId, text, userId) {
  try {
    console.log(`🧠 Processing document ${documentId} with AI...`);
    
    // Generate summary and key points
    const analysis = await aiService.analyzeDocument(text);
    
    // Update document in database
    await dbService.updateDocumentAnalysis(documentId, analysis);
    
    // Award XP for document upload
    await gamificationService.addExperience(userId, 50, 'document_upload');
    
    console.log(`✅ Document ${documentId} processed successfully`);
  } catch (error) {
    console.error(`❌ Error processing document ${documentId}:`, error);
  }
}

// Get documents for user
app.get('/api/documents/:userId', async (req, res) => {
  try {
    const documents = await dbService.getUserDocuments(req.params.userId);
    res.json({ success: true, documents });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get specific document
app.get('/api/documents/detail/:documentId', async (req, res) => {
  try {
    const document = await dbService.getDocument(req.params.documentId);
    res.json({ success: true, document });
  } catch (error) {
    res.status(404).json({ success: false, error: error.message });
  }
});

// Chat endpoint
app.post('/api/chat', async (req, res) => {
  try {
    const { message, userId, language = 'en', conversationHistory = [] } = req.body;
    
    console.log(`💬 Chat request from user ${userId}: ${message}`);
    
    // Get user's documents for context
    const userDocuments = await dbService.getUserDocuments(userId);
    const context = userDocuments.map(doc => doc.extracted_text).join('\n\n');
    
    // Generate AI response
    const response = await aiService.generateChatResponse(message, context, conversationHistory, language);
    
    // Award XP for chat interaction
    await gamificationService.addExperience(userId, 5, 'chat_message');
    
    res.json({
      success: true,
      response: response.message,
      emotion: response.emotion || 'neutral',
      suggestions: response.suggestions || []
    });

  } catch (error) {
    console.error('❌ Chat error:', error);
    res.status(500).json({ 
      success: false, 
      error: 'I apologize, but I encountered an error. Please try again.',
      response: 'I apologize, but I encountered an error. Please try again.'
    });
  }
});

// Summarization endpoint
app.post('/api/summarize', async (req, res) => {
  try {
    const { documentIds, userId, language = 'en' } = req.body;
    
    // Get documents
    const documents = await Promise.all(
      documentIds.map(id => dbService.getDocument(id))
    );
    
    const combinedText = documents.map(doc => doc.extracted_text).join('\n\n');
    const summary = await aiService.generateSummary(combinedText, language);
    
    // Award XP
    await gamificationService.addExperience(userId, 25, 'document_summary');
    
    res.json({ success: true, summary });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Quiz generation endpoint
app.post('/api/quiz', async (req, res) => {
  try {
    const { documentIds, userId, difficulty = 'medium', questionCount = 5 } = req.body;
    
    // Get documents
    const documents = await Promise.all(
      documentIds.map(id => dbService.getDocument(id))
    );
    
    const combinedText = documents.map(doc => doc.extracted_text).join('\n\n');
    const quiz = await aiService.generateQuiz(combinedText, difficulty, questionCount);
    
    // Award XP
    await gamificationService.addExperience(userId, 30, 'quiz_generation');
    
    res.json({ success: true, quiz });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Text-to-Speech endpoint
app.post('/api/tts', async (req, res) => {
  try {
    const { text, language = 'en-US', voice = 'default' } = req.body;
    
    console.log(`🔊 TTS request: ${text.substring(0, 50)}...`);
    
    const audioBuffer = await ttsService.synthesizeSpeech(text, language, voice);
    
    res.set({
      'Content-Type': 'audio/mpeg',
      'Content-Length': audioBuffer.length
    });
    
    res.send(audioBuffer);
    
  } catch (error) {
    console.error('❌ TTS error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Speech-to-Text endpoint
app.post('/api/stt', upload.single('audio'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, error: 'No audio file provided' });
    }
    
    const language = req.body.language || 'en-US';
    console.log(`🎤 STT request for language: ${language}`);
    
    const transcript = await ttsService.transcribeAudio(req.file.path, language);
    
    // Clean up uploaded audio file
    fs.unlinkSync(req.file.path);
    
    res.json({ success: true, transcript });
    
  } catch (error) {
    console.error('❌ STT error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Gamification endpoints
app.get('/api/gamification/progress/:userId', async (req, res) => {
  try {
    const progress = await gamificationService.getUserProgress(req.params.userId);
    res.json({ success: true, progress });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/gamification/award-xp', async (req, res) => {
  try {
    const { userId, points, activity } = req.body;
    const result = await gamificationService.addExperience(userId, points, activity);
    res.json({ success: true, result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/gamification/achievements/:userId', async (req, res) => {
  try {
    const achievements = await gamificationService.getUserAchievements(req.params.userId);
    res.json({ success: true, achievements });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('❌ Server error:', error);
  
  if (error instanceof multer.MulterError) {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        success: false,
        error: 'File too large. Maximum size is 10MB.'
      });
    }
  }
  
  res.status(500).json({
    success: false,
    error: process.env.NODE_ENV === 'development' ? error.message : 'Internal server error'
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found'
  });
});

// Start server
async function startServer() {
  try {
    await initializeServices();
    
    app.listen(PORT, () => {
      console.log(`\n🚀 AI Educational Avatar Backend`);
      console.log(`📡 Server running on http://localhost:${PORT}`);
      console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
      console.log(`📁 Upload directory: ${path.resolve('./uploads')}`);
      console.log(`🗄️  Database: ${path.resolve(process.env.DATABASE_PATH || './database/education.db')}`);
      console.log(`\n✅ Backend is ready to serve your AI avatar!`);
      console.log(`\n📋 Available endpoints:`);
      console.log(`   GET  /api/health - Health check`);
      console.log(`   POST /api/documents/upload - Upload documents`);
      console.log(`   POST /api/chat - AI chat`);
      console.log(`   POST /api/tts - Text-to-speech`);
      console.log(`   POST /api/stt - Speech-to-text`);
      console.log(`   GET  /api/gamification/progress/:userId - User progress`);
    });
    
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n🛑 Shutting down server...');
  if (dbService) {
    await dbService.close();
  }
  console.log('✅ Server shut down gracefully');
  process.exit(0);
});

startServer();