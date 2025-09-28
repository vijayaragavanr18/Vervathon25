const OpenAI = require('openai');

class AIService {
  constructor() {
    if (!process.env.OPENAI_API_KEY) {
      throw new Error('OPENAI_API_KEY environment variable is required');
    }
    
    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY
    });
    
    this.model = process.env.OPENAI_MODEL || 'gpt-4';
    this.maxTokens = parseInt(process.env.MAX_TOKENS) || 2000;
    this.temperature = parseFloat(process.env.TEMPERATURE) || 0.7;
  }

  async generateChatResponse(userMessage, context = '', conversationHistory = [], language = 'en') {
    try {
      console.log(`🧠 Generating chat response for language: ${language}`);
      
      // Build the system prompt
      const systemPrompt = this.buildSystemPrompt(language, context);
      
      // Build message history
      const messages = [
        { role: 'system', content: systemPrompt },
        ...conversationHistory.slice(-10), // Keep last 10 messages for context
        { role: 'user', content: userMessage }
      ];
      
      const response = await this.openai.chat.completions.create({
        model: this.model,
        messages: messages,
        max_tokens: this.maxTokens,
        temperature: this.temperature,
        response_format: { type: 'json_object' }
      });
      
      const result = JSON.parse(response.choices[0].message.content);
      
      return {
        message: result.response || result.message || 'I apologize, but I encountered an issue generating a response.',
        emotion: result.emotion || 'neutral',
        suggestions: result.suggestions || []
      };
      
    } catch (error) {
      console.error('❌ AI Service error:', error);
      
      // Fallback response based on language
      const fallbackResponses = {
        en: "I apologize, but I'm having trouble processing your request right now. Please try again.",
        es: "Lo siento, pero tengo problemas para procesar tu solicitud ahora. Por favor, inténtalo de nuevo.",
        fr: "Je m'excuse, mais j'ai des difficultés à traiter votre demande en ce moment. Veuillez réessayer.",
        de: "Entschuldigung, aber ich habe Schwierigkeiten, Ihre Anfrage zu bearbeiten. Bitte versuchen Sie es erneut.",
        it: "Mi scuso, ma sto avendo difficoltà a elaborare la tua richiesta. Per favore riprova.",
        pt: "Peço desculpa, mas estou tendo dificuldades para processar seu pedido. Por favor, tente novamente.",
        zh: "抱歉，我现在处理您的请求时遇到了问题。请重试。",
        ja: "申し訳ありませんが、現在リクエストの処理に問題があります。もう一度お試しください。"
      };
      
      return {
        message: fallbackResponses[language] || fallbackResponses.en,
        emotion: 'concerned',
        suggestions: ['Try rephrasing your question', 'Check your internet connection']
      };
    }
  }

  buildSystemPrompt(language, context) {
    const languageInstructions = {
      en: 'Respond in English',
      es: 'Responde en español',
      fr: 'Répondez en français',
      de: 'Antworten Sie auf Deutsch',
      it: 'Rispondi in italiano',
      pt: 'Responda em português',
      zh: '用中文回答',
      ja: '日本語で答えてください'
    };

    const contextSection = context ? `

AVAILABLE DOCUMENTS CONTEXT:
${context.substring(0, 4000)}
${context.length > 4000 ? '\n[Context truncated...]' : ''}` : '';

    return `You are an AI educational avatar assistant that helps students learn and understand their study materials. ${languageInstructions[language] || languageInstructions.en}.

PERSONALITY:
- Friendly, encouraging, and supportive
- Professional but approachable
- Enthusiastic about learning
- Patient with student questions
- Adaptable to different learning styles

CAPABILITIES:
- Answer questions about uploaded documents
- Provide explanations and summaries
- Generate study materials and quizzes
- Offer learning strategies and tips
- Support multiple languages

RESPONSE FORMAT:
Always respond with a JSON object containing:
{
  "response": "Your helpful response here",
  "emotion": "neutral|happy|excited|thoughtful|concerned|encouraging",
  "suggestions": ["suggestion1", "suggestion2", "suggestion3"]
}

EMOTION GUIDELINES:
- happy: For positive interactions, achievements, correct answers
- excited: When discussing interesting topics or breakthroughs
- thoughtful: For complex questions requiring deep thinking
- concerned: When addressing difficulties or problems
- encouraging: When motivating students or providing support
- neutral: For general information sharing${contextSection}

INSTRUCTIONS:
1. Use the document context to provide accurate, relevant answers
2. If you don't know something, be honest about it
3. Encourage active learning and critical thinking
4. Provide practical examples when possible
5. Keep responses concise but informative
6. Always include helpful suggestions for further learning`;
  }

  async analyzeDocument(text) {
    try {
      console.log('🔍 Analyzing document with AI...');
      
      const prompt = `Analyze the following document and provide a comprehensive analysis. Return your response as a JSON object with the following structure:

{
  "summary": "A concise summary of the main content (2-3 sentences)",
  "keyPoints": ["point1", "point2", "point3", "point4", "point5"],
  "topics": ["topic1", "topic2", "topic3"],
  "difficulty": "beginner|intermediate|advanced",
  "estimatedReadingTime": "X minutes",
  "learningObjectives": ["objective1", "objective2", "objective3"]
}

Document content:
${text.substring(0, 8000)}${text.length > 8000 ? '\n[Content truncated...]' : ''}`;

      const response = await this.openai.chat.completions.create({
        model: this.model,
        messages: [
          { role: 'system', content: 'You are an expert document analyst. Provide structured analysis in JSON format.' },
          { role: 'user', content: prompt }
        ],
        max_tokens: 1500,
        temperature: 0.3,
        response_format: { type: 'json_object' }
      });

      return JSON.parse(response.choices[0].message.content);
      
    } catch (error) {
      console.error('❌ Document analysis error:', error);
      return {
        summary: 'Document uploaded successfully but detailed analysis is temporarily unavailable.',
        keyPoints: ['Content analysis pending', 'Full text extracted', 'Ready for questions'],
        topics: ['General content'],
        difficulty: 'intermediate',
        estimatedReadingTime: '5-10 minutes',
        learningObjectives: ['Review content', 'Ask specific questions', 'Request summaries']
      };
    }
  }

  async generateSummary(text, language = 'en', length = 'medium') {
    try {
      console.log(`📝 Generating ${length} summary in ${language}...`);
      
      const lengthInstructions = {
        short: 'Provide a brief summary in 2-3 sentences',
        medium: 'Provide a comprehensive summary in 1-2 paragraphs',
        long: 'Provide a detailed summary with multiple sections and key details'
      };
      
      const languageInstructions = {
        en: 'Write in English',
        es: 'Escribe en español',
        fr: 'Écrivez en français',
        de: 'Schreiben Sie auf Deutsch',
        it: 'Scrivi in italiano',
        pt: 'Escreva em português',
        zh: '用中文写',
        ja: '日本語で書いてください'
      };

      const prompt = `${lengthInstructions[length] || lengthInstructions.medium}. ${languageInstructions[language] || languageInstructions.en}.

Text to summarize:
${text.substring(0, 10000)}${text.length > 10000 ? '\n[Content truncated...]' : ''}`;

      const response = await this.openai.chat.completions.create({
        model: this.model,
        messages: [
          { 
            role: 'system', 
            content: `You are an expert at creating clear, informative summaries. Focus on the main ideas, key concepts, and important details. Make the summary educational and easy to understand.` 
          },
          { role: 'user', content: prompt }
        ],
        max_tokens: length === 'long' ? 1500 : length === 'medium' ? 800 : 400,
        temperature: 0.3
      });

      return response.choices[0].message.content.trim();
      
    } catch (error) {
      console.error('❌ Summary generation error:', error);
      const fallback = {
        en: 'Summary generation is temporarily unavailable. Please try again later.',
        es: 'La generación de resúmenes no está disponible temporalmente. Inténtelo de nuevo más tarde.',
        fr: 'La génération de résumés est temporairement indisponible. Veuillez réessayer plus tard.',
        de: 'Die Zusammenfassungsgenerierung ist vorübergehend nicht verfügbar. Bitte versuchen Sie es später erneut.',
        it: 'La generazione di riassunti è temporaneamente non disponibile. Riprova più tardi.',
        pt: 'A geração de resumos está temporariamente indisponível. Tente novamente mais tarde.',
        zh: '摘要生成暂时不可用。请稍后再试。',
        ja: '要約の生成は一時的に利用できません。後でもう一度お試しください。'
      };
      return fallback[language] || fallback.en;
    }
  }

  async generateQuiz(text, difficulty = 'medium', questionCount = 5) {
    try {
      console.log(`❓ Generating ${questionCount} ${difficulty} quiz questions...`);
      
      const difficultyInstructions = {
        easy: 'Create basic recall questions that test fundamental understanding',
        medium: 'Create questions that require understanding and application of concepts',
        hard: 'Create challenging questions that require analysis, synthesis, and critical thinking'
      };

      const prompt = `Create a quiz with ${questionCount} multiple-choice questions based on the following content. 
      
Difficulty: ${difficulty} - ${difficultyInstructions[difficulty]}

Return your response as a JSON object with this structure:
{
  "title": "Quiz Title",
  "difficulty": "${difficulty}",
  "questions": [
    {
      "id": 1,
      "question": "Question text here?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correctAnswer": 0,
      "explanation": "Why this answer is correct"
    }
  ]
}

Content:
${text.substring(0, 8000)}${text.length > 8000 ? '\n[Content truncated...]' : ''}`;

      const response = await this.openai.chat.completions.create({
        model: this.model,
        messages: [
          { 
            role: 'system', 
            content: 'You are an expert educational content creator specializing in creating engaging, well-structured quizzes that effectively test comprehension.' 
          },
          { role: 'user', content: prompt }
        ],
        max_tokens: 2000,
        temperature: 0.4,
        response_format: { type: 'json_object' }
      });

      return JSON.parse(response.choices[0].message.content);
      
    } catch (error) {
      console.error('❌ Quiz generation error:', error);
      
      // Fallback quiz
      return {
        title: 'Sample Quiz',
        difficulty: difficulty,
        questions: [
          {
            id: 1,
            question: 'Based on the uploaded content, which statement best describes the main topic?',
            options: [
              'The content covers multiple educational topics',
              'The content is not related to education',
              'The content requires further analysis',
              'The content is incomplete'
            ],
            correctAnswer: 0,
            explanation: 'Quiz generation encountered an error. Please try again or contact support.'
          }
        ]
      };
    }
  }

  async generateStudyPlan(documents, userLevel = 'intermediate', timeframe = '1 week') {
    try {
      console.log(`📚 Generating ${timeframe} study plan for ${userLevel} level...`);
      
      const documentSummaries = documents.map(doc => ({
        title: doc.filename,
        summary: doc.summary || 'Content analysis pending',
        topics: doc.topics ? JSON.parse(doc.topics) : []
      }));

      const prompt = `Create a personalized study plan based on the following documents:

${documentSummaries.map(doc => `
Document: ${doc.title}
Summary: ${doc.summary}
Topics: ${doc.topics.join(', ')}
`).join('\n')}

User Level: ${userLevel}
Timeframe: ${timeframe}

Return a JSON object with this structure:
{
  "title": "Study Plan Title",
  "duration": "${timeframe}",
  "difficulty": "${userLevel}",
  "dailySchedule": [
    {
      "day": 1,
      "tasks": ["task1", "task2"],
      "estimatedTime": "X hours",
      "focus": "topic focus"
    }
  ],
  "learningGoals": ["goal1", "goal2"],
  "assessmentSchedule": ["assessment1", "assessment2"]
}`;

      const response = await this.openai.chat.completions.create({
        model: this.model,
        messages: [
          { 
            role: 'system', 
            content: 'You are an expert educational consultant who creates effective, personalized study plans that optimize learning outcomes.' 
          },
          { role: 'user', content: prompt }
        ],
        max_tokens: 1500,
        temperature: 0.5,
        response_format: { type: 'json_object' }
      });

      return JSON.parse(response.choices[0].message.content);
      
    } catch (error) {
      console.error('❌ Study plan generation error:', error);
      
      return {
        title: 'Basic Study Plan',
        duration: timeframe,
        difficulty: userLevel,
        dailySchedule: [
          {
            day: 1,
            tasks: ['Review uploaded documents', 'Take notes on key concepts'],
            estimatedTime: '2 hours',
            focus: 'Initial review and comprehension'
          }
        ],
        learningGoals: ['Understand main concepts', 'Identify key topics', 'Prepare for assessment'],
        assessmentSchedule: ['Mid-point quiz', 'Final comprehensive test']
      };
    }
  }

  async generateFlashcards(text, count = 10) {
    try {
      console.log(`🃏 Generating ${count} flashcards...`);
      
      const prompt = `Create ${count} educational flashcards based on the following content. Focus on key concepts, definitions, and important facts.

Return a JSON object with this structure:
{
  "flashcards": [
    {
      "id": 1,
      "front": "Question or concept",
      "back": "Answer or explanation"
    }
  ]
}

Content:
${text.substring(0, 6000)}${text.length > 6000 ? '\n[Content truncated...]' : ''}`;

      const response = await this.openai.chat.completions.create({
        model: this.model,
        messages: [
          { 
            role: 'system', 
            content: 'You are an expert at creating effective flashcards that help students memorize and understand key concepts.' 
          },
          { role: 'user', content: prompt }
        ],
        max_tokens: 1500,
        temperature: 0.3,
        response_format: { type: 'json_object' }
      });

      return JSON.parse(response.choices[0].message.content);
      
    } catch (error) {
      console.error('❌ Flashcard generation error:', error);
      
      return {
        flashcards: [
          {
            id: 1,
            front: 'What is the main topic of the uploaded document?',
            back: 'The document contains educational content that requires further analysis.'
          }
        ]
      };
    }
  }

  // Utility method to check API status
  async checkAPIStatus() {
    try {
      const response = await this.openai.chat.completions.create({
        model: 'gpt-3.5-turbo',
        messages: [{ role: 'user', content: 'Hello' }],
        max_tokens: 5
      });
      
      return { 
        status: 'healthy', 
        model: this.model,
        responseTime: Date.now()
      };
      
    } catch (error) {
      return { 
        status: 'error', 
        error: error.message,
        model: this.model
      };
    }
  }
}

module.exports = AIService;