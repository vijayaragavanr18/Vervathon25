# 🚀 AI Educational Avatar - Backend Setup Guide

## 📋 **QUICK START - What You Need**

### **1. Required API Keys:**

#### **🤖 OpenAI API Key (ESSENTIAL)**
- **Where to get:** https://platform.openai.com/api-keys
- **Cost:** Pay-per-use (approximately $0.002/1K tokens for GPT-4)
- **Used for:** AI chat, document analysis, quiz generation, summaries
- **Status:** ⚠️ **REQUIRED** - Backend won't work without this

#### **🗣️ Google Cloud API Keys (REQUIRED for voice features)**
- **Where to get:** https://console.cloud.google.com/
- **Services needed:**
  - Text-to-Speech API
  - Speech-to-Text API
- **Cost:** Free tier available (1M characters/month TTS, 60 minutes/month STT)
- **Status:** ⚠️ **REQUIRED** for voice features

### **2. Installation Steps:**

```bash
# 1. Navigate to backend directory
cd backend

# 2. Install dependencies
npm install

# 3. Set up environment variables
# Copy .env file and add your API keys
# Edit the .env file with your actual API keys

# 4. Start the server
npm start
```

## 🔧 **Detailed Setup Instructions**

### **Step 1: Get OpenAI API Key**
1. Go to https://platform.openai.com/api-keys
2. Create account or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. Add to `.env` file: `OPENAI_API_KEY=sk-your-key-here`

### **Step 2: Setup Google Cloud (for voice features)**
1. Go to https://console.cloud.google.com/
2. Create new project or select existing
3. Enable these APIs:
   - Cloud Text-to-Speech API
   - Cloud Speech-to-Text API
4. Create service account:
   - IAM & Admin → Service Accounts
   - Create Service Account
   - Download JSON key file
5. Place JSON file in backend folder as `google-cloud-key.json`
6. Add to `.env`: `GOOGLE_CLOUD_KEY_FILE=./google-cloud-key.json`

### **Step 3: Configure Environment**
Edit the `.env` file with your values:

```env
# REQUIRED - Your actual OpenAI API key
OPENAI_API_KEY=sk-your-openai-key-here

# REQUIRED - Path to your Google Cloud key file
GOOGLE_CLOUD_KEY_FILE=./google-cloud-key.json

# OPTIONAL - Customize other settings
PORT=3001
OPENAI_MODEL=gpt-4
DATABASE_PATH=./database/education.db
```

## 📊 **Cost Estimate**

### **OpenAI API Costs:**
- **GPT-4:** ~$0.03 per 1K tokens (input) + $0.06 per 1K tokens (output)
- **Average chat message:** ~$0.01-0.05
- **Document analysis:** ~$0.10-0.50 per document
- **Monthly estimate:** $10-50 for moderate use

### **Google Cloud Costs:**
- **Text-to-Speech:** Free up to 1M characters/month
- **Speech-to-Text:** Free up to 60 minutes/month
- **Monthly estimate:** $0-10 for moderate use

### **Total Monthly Cost:** $10-60 for moderate usage

## 🎯 **Available API Endpoints**

Once running, your backend provides:

```
POST /api/documents/upload     - Upload documents (PDF, DOCX, etc.)
POST /api/chat                 - AI chat conversations
POST /api/tts                  - Text-to-speech
POST /api/stt                  - Speech-to-text
POST /api/quiz                 - Generate quizzes
POST /api/summarize           - Document summaries
GET  /api/gamification/progress/:userId - User progress
POST /api/user/create         - Create new user
GET  /api/health              - Health check
```

## 🔍 **Testing the Setup**

### **1. Start the server:**
```bash
cd backend
npm start
```

### **2. Test health endpoint:**
Open browser: `http://localhost:3001/api/health`

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "version": "1.0.0"
}
```

### **3. Test document upload:**
```bash
curl -X POST http://localhost:3001/api/documents/upload \
  -F "document=@your-file.pdf" \
  -F "userId=test-user"
```

## ⚡ **Features Included**

### **✅ Document Processing**
- PDF, DOCX, Excel, PowerPoint, TXT support
- Text extraction and analysis
- AI-powered summarization

### **✅ AI Chat System**
- Multi-language support (8 languages)
- Context-aware responses
- Conversation history

### **✅ Voice Features**
- Text-to-Speech in multiple languages
- Speech-to-Text recognition
- Voice-controlled interface

### **✅ Gamification System**
- XP points and levels
- Achievement badges
- Learning streaks
- Leaderboards

### **✅ User Management**
- User profiles and progress tracking
- Study statistics
- Personal learning dashboard

## 🛠️ **Troubleshooting**

### **Common Issues:**

#### **"OpenAI API error"**
- Check if API key is correct
- Verify you have credits in OpenAI account
- Check internet connection

#### **"Google Cloud authentication failed"**
- Verify JSON key file path
- Check if APIs are enabled
- Confirm project ID is correct

#### **"Database error"**
- Delete `database` folder and restart
- Check file permissions
- Ensure SQLite3 is properly installed

#### **Port already in use:**
```bash
# Change port in .env file
PORT=3002
```

## 🔄 **Development Mode**

For development with auto-restart:
```bash
npm run dev
```

## 📝 **Next Steps**

1. **Get your API keys** (OpenAI + Google Cloud)
2. **Edit the `.env` file** with your keys
3. **Run `npm install`** to install dependencies
4. **Run `npm start`** to start the server
5. **Test with health endpoint** at http://localhost:3001/api/health
6. **Connect your frontend** to the backend
7. **Start uploading documents and chatting!**

Your backend is now fully configured and ready to power your AI Educational Avatar! 🚀

The frontend you have is already perfect and will connect automatically to these backend endpoints.