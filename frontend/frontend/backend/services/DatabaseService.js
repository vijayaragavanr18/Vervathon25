const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs-extra');

class DatabaseService {
  constructor() {
    this.dbPath = process.env.DATABASE_PATH || './database/education.db';
    this.db = null;
  }

  async initialize() {
    try {
      // Ensure database directory exists
      await fs.ensureDir(path.dirname(this.dbPath));
      
      // Connect to database
      this.db = new sqlite3.Database(this.dbPath);
      
      // Enable foreign keys
      await this.run('PRAGMA foreign_keys = ON');
      
      // Create tables
      await this.createTables();
      
      console.log('✅ Database initialized successfully');
    } catch (error) {
      console.error('❌ Database initialization failed:', error);
      throw error;
    }
  }

  async createTables() {
    const tables = [
      // Users table
      `CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )`,

      // Documents table
      `CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        extracted_text TEXT,
        summary TEXT,
        key_points TEXT,
        topics TEXT,
        processed BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
      )`,

      // Chat sessions table
      `CREATE TABLE IF NOT EXISTS chat_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
      )`,

      // Chat messages table
      `CREATE TABLE IF NOT EXISTS chat_messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        message TEXT NOT NULL,
        response TEXT NOT NULL,
        language TEXT DEFAULT 'en',
        emotion TEXT DEFAULT 'neutral',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
      )`,

      // Quiz sessions table
      `CREATE TABLE IF NOT EXISTS quiz_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        document_ids TEXT NOT NULL,
        questions TEXT NOT NULL,
        answers TEXT,
        score INTEGER DEFAULT 0,
        completed BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
      )`,

      // Achievements table
      `CREATE TABLE IF NOT EXISTS achievements (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        achievement_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        xp_reward INTEGER DEFAULT 0,
        unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
      )`,

      // XP transactions table
      `CREATE TABLE IF NOT EXISTS xp_transactions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        activity_type TEXT NOT NULL,
        xp_earned INTEGER NOT NULL,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
      )`
    ];

    for (const table of tables) {
      await this.run(table);
    }

    // Create indexes for better performance
    const indexes = [
      'CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id)',
      'CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)',
      'CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)',
      'CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_id ON quiz_sessions(user_id)',
      'CREATE INDEX IF NOT EXISTS idx_achievements_user_id ON achievements(user_id)',
      'CREATE INDEX IF NOT EXISTS idx_xp_transactions_user_id ON xp_transactions(user_id)'
    ];

    for (const index of indexes) {
      await this.run(index);
    }
  }

  // Promise wrapper for db.run
  run(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.run(sql, params, function(err) {
        if (err) reject(err);
        else resolve({ id: this.lastID, changes: this.changes });
      });
    });
  }

  // Promise wrapper for db.get
  get(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.get(sql, params, (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
  }

  // Promise wrapper for db.all
  all(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.all(sql, params, (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });
  }

  // User operations
  async createUser(id, username, email) {
    try {
      await this.run(
        'INSERT INTO users (id, username, email) VALUES (?, ?, ?)',
        [id, username, email]
      );
      return await this.getUser(id);
    } catch (error) {
      throw new Error(`Failed to create user: ${error.message}`);
    }
  }

  async getUser(id) {
    const user = await this.get('SELECT * FROM users WHERE id = ?', [id]);
    if (!user) {
      throw new Error('User not found');
    }
    return user;
  }

  async updateUserXP(userId, xp) {
    const user = await this.getUser(userId);
    const newXP = user.xp + xp;
    const newLevel = Math.floor(newXP / 100) + 1; // Every 100 XP = 1 level

    await this.run(
      'UPDATE users SET xp = ?, level = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
      [newXP, newLevel, userId]
    );

    return { xp: newXP, level: newLevel, levelUp: newLevel > user.level };
  }

  // Document operations
  async saveDocument(documentData) {
    const { v4: uuidv4 } = require('uuid');
    const id = uuidv4();
    
    await this.run(
      `INSERT INTO documents 
       (id, user_id, filename, file_path, file_type, file_size, extracted_text) 
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [
        id,
        documentData.userId,
        documentData.filename,
        documentData.filePath,
        documentData.fileType,
        documentData.fileSize,
        documentData.extractedText
      ]
    );

    return await this.getDocument(id);
  }

  async getDocument(id) {
    const document = await this.get('SELECT * FROM documents WHERE id = ?', [id]);
    if (!document) {
      throw new Error('Document not found');
    }
    return document;
  }

  async getUserDocuments(userId) {
    return await this.all(
      'SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC',
      [userId]
    );
  }

  async updateDocumentAnalysis(documentId, analysis) {
    await this.run(
      `UPDATE documents 
       SET summary = ?, key_points = ?, topics = ?, processed = TRUE 
       WHERE id = ?`,
      [
        analysis.summary,
        JSON.stringify(analysis.keyPoints),
        JSON.stringify(analysis.topics),
        documentId
      ]
    );
  }

  // Chat operations
  async createChatSession(userId, title = null) {
    const { v4: uuidv4 } = require('uuid');
    const id = uuidv4();
    
    await this.run(
      'INSERT INTO chat_sessions (id, user_id, title) VALUES (?, ?, ?)',
      [id, userId, title || `Chat ${new Date().toLocaleString()}`]
    );

    return id;
  }

  async saveChatMessage(sessionId, message, response, language = 'en', emotion = 'neutral') {
    const { v4: uuidv4 } = require('uuid');
    const id = uuidv4();
    
    await this.run(
      `INSERT INTO chat_messages 
       (id, session_id, message, response, language, emotion) 
       VALUES (?, ?, ?, ?, ?, ?)`,
      [id, sessionId, message, response, language, emotion]
    );

    return id;
  }

  async getChatHistory(sessionId) {
    return await this.all(
      'SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC',
      [sessionId]
    );
  }

  async getUserChatSessions(userId) {
    return await this.all(
      'SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC',
      [userId]
    );
  }

  // Quiz operations
  async saveQuizSession(userId, documentIds, questions) {
    const { v4: uuidv4 } = require('uuid');
    const id = uuidv4();
    
    await this.run(
      `INSERT INTO quiz_sessions 
       (id, user_id, document_ids, questions) 
       VALUES (?, ?, ?, ?)`,
      [id, userId, JSON.stringify(documentIds), JSON.stringify(questions)]
    );

    return id;
  }

  async updateQuizResults(quizId, answers, score) {
    await this.run(
      'UPDATE quiz_sessions SET answers = ?, score = ?, completed = TRUE WHERE id = ?',
      [JSON.stringify(answers), score, quizId]
    );
  }

  async getUserQuizzes(userId) {
    return await this.all(
      'SELECT * FROM quiz_sessions WHERE user_id = ? ORDER BY created_at DESC',
      [userId]
    );
  }

  // Achievement operations
  async addAchievement(userId, achievementType, title, description, xpReward = 0) {
    const { v4: uuidv4 } = require('uuid');
    const id = uuidv4();
    
    // Check if achievement already exists
    const existing = await this.get(
      'SELECT id FROM achievements WHERE user_id = ? AND achievement_type = ?',
      [userId, achievementType]
    );

    if (existing) {
      return null; // Already unlocked
    }

    await this.run(
      `INSERT INTO achievements 
       (id, user_id, achievement_type, title, description, xp_reward) 
       VALUES (?, ?, ?, ?, ?, ?)`,
      [id, userId, achievementType, title, description, xpReward]
    );

    return id;
  }

  async getUserAchievements(userId) {
    return await this.all(
      'SELECT * FROM achievements WHERE user_id = ? ORDER BY unlocked_at DESC',
      [userId]
    );
  }

  // XP transaction operations
  async addXPTransaction(userId, activityType, xpEarned, description = null) {
    const { v4: uuidv4 } = require('uuid');
    const id = uuidv4();
    
    await this.run(
      `INSERT INTO xp_transactions 
       (id, user_id, activity_type, xp_earned, description) 
       VALUES (?, ?, ?, ?, ?)`,
      [id, userId, activityType, xpEarned, description]
    );

    return id;
  }

  async getUserXPTransactions(userId) {
    return await this.all(
      'SELECT * FROM xp_transactions WHERE user_id = ? ORDER BY created_at DESC',
      [userId]
    );
  }

  // Statistics
  async getUserStats(userId) {
    const stats = {};
    
    // Basic user info
    stats.user = await this.getUser(userId);
    
    // Document stats
    const docStats = await this.get(
      `SELECT 
         COUNT(*) as total_documents,
         SUM(file_size) as total_size,
         COUNT(CASE WHEN processed = TRUE THEN 1 END) as processed_documents
       FROM documents WHERE user_id = ?`,
      [userId]
    );
    stats.documents = docStats;
    
    // Chat stats
    const chatStats = await this.get(
      `SELECT 
         COUNT(DISTINCT cs.id) as total_sessions,
         COUNT(cm.id) as total_messages
       FROM chat_sessions cs
       LEFT JOIN chat_messages cm ON cs.id = cm.session_id
       WHERE cs.user_id = ?`,
      [userId]
    );
    stats.chat = chatStats;
    
    // Quiz stats
    const quizStats = await this.get(
      `SELECT 
         COUNT(*) as total_quizzes,
         COUNT(CASE WHEN completed = TRUE THEN 1 END) as completed_quizzes,
         AVG(CASE WHEN completed = TRUE THEN score END) as average_score
       FROM quiz_sessions WHERE user_id = ?`,
      [userId]
    );
    stats.quiz = quizStats;
    
    // Achievement stats
    const achievementStats = await this.get(
      'SELECT COUNT(*) as total_achievements FROM achievements WHERE user_id = ?',
      [userId]
    );
    stats.achievements = achievementStats;
    
    return stats;
  }

  // Close database connection
  async close() {
    return new Promise((resolve) => {
      if (this.db) {
        this.db.close((err) => {
          if (err) console.error('Error closing database:', err);
          else console.log('✅ Database connection closed');
          resolve();
        });
      } else {
        resolve();
      }
    });
  }
}

module.exports = DatabaseService;