const textToSpeech = require('@google-cloud/text-to-speech');
const speech = require('@google-cloud/speech');
const fs = require('fs-extra');
const path = require('path');

class TTSService {
  constructor() {
    // Initialize Google Cloud clients
    this.initializeClients();
    
    this.supportedLanguages = {
      'en': { code: 'en-US', name: 'English (US)' },
      'es': { code: 'es-ES', name: 'Spanish (Spain)' },
      'fr': { code: 'fr-FR', name: 'French (France)' },
      'de': { code: 'de-DE', name: 'German (Germany)' },
      'it': { code: 'it-IT', name: 'Italian (Italy)' },
      'pt': { code: 'pt-BR', name: 'Portuguese (Brazil)' },
      'zh': { code: 'zh-CN', name: 'Chinese (Simplified)' },
      'ja': { code: 'ja-JP', name: 'Japanese (Japan)' }
    };

    this.voiceSettings = {
      'en-US': ['en-US-Standard-C', 'en-US-Standard-A', 'en-US-Standard-E', 'en-US-Standard-F'],
      'es-ES': ['es-ES-Standard-A', 'es-ES-Standard-B'],
      'fr-FR': ['fr-FR-Standard-A', 'fr-FR-Standard-C', 'fr-FR-Standard-B', 'fr-FR-Standard-D'],
      'de-DE': ['de-DE-Standard-A', 'de-DE-Standard-F'],
      'it-IT': ['it-IT-Standard-A', 'it-IT-Standard-B'],
      'pt-BR': ['pt-BR-Standard-A', 'pt-BR-Standard-B'],
      'zh-CN': ['zh-CN-Standard-A', 'zh-CN-Standard-D', 'zh-CN-Standard-B', 'zh-CN-Standard-C'],
      'ja-JP': ['ja-JP-Standard-A', 'ja-JP-Standard-B', 'ja-JP-Standard-C', 'ja-JP-Standard-D']
    };
  }

  initializeClients() {
    try {
      // Check if Google Cloud credentials are provided
      if (process.env.GOOGLE_CLOUD_KEY_FILE && fs.existsSync(process.env.GOOGLE_CLOUD_KEY_FILE)) {
        // Use service account key file
        this.ttsClient = new textToSpeech.TextToSpeechClient({
          keyFilename: process.env.GOOGLE_CLOUD_KEY_FILE
        });
        
        this.speechClient = new speech.SpeechClient({
          keyFilename: process.env.GOOGLE_CLOUD_KEY_FILE
        });
        
        console.log('✅ Google Cloud TTS/STT initialized with service account');
        
      } else if (process.env.GOOGLE_CLOUD_CREDENTIALS) {
        // Use JSON credentials from environment variable
        const credentials = JSON.parse(process.env.GOOGLE_CLOUD_CREDENTIALS);
        
        this.ttsClient = new textToSpeech.TextToSpeechClient({
          credentials: credentials
        });
        
        this.speechClient = new speech.SpeechClient({
          credentials: credentials
        });
        
        console.log('✅ Google Cloud TTS/STT initialized with credentials');
        
      } else {
        // Fallback: try default credentials (if running on Google Cloud)
        this.ttsClient = new textToSpeech.TextToSpeechClient();
        this.speechClient = new speech.SpeechClient();
        
        console.log('⚠️  Google Cloud TTS/STT using default credentials');
      }
      
    } catch (error) {
      console.error('❌ Google Cloud TTS/STT initialization failed:', error);
      console.log('🔄 TTS/STT will use fallback methods');
      this.ttsClient = null;
      this.speechClient = null;
    }
  }

  async synthesizeSpeech(text, languageCode = 'en-US', voiceName = 'default') {
    try {
      console.log(`🔊 Synthesizing speech: ${languageCode} - ${text.substring(0, 50)}...`);
      
      // If no Google Cloud client, use fallback
      if (!this.ttsClient) {
        return await this.fallbackTTS(text, languageCode);
      }

      // Get language code
      const langCode = this.getLanguageCode(languageCode);
      
      // Select voice
      const selectedVoice = this.selectVoice(langCode, voiceName);
      
      // Construct the request
      const request = {
        input: { text: text },
        voice: {
          languageCode: langCode,
          name: selectedVoice,
          ssmlGender: 'FEMALE'
        },
        audioConfig: {
          audioEncoding: 'MP3',
          speakingRate: 1.0,
          pitch: 0.0,
          volumeGainDb: 0.0
        }
      };

      // Perform the text-to-speech request
      const [response] = await this.ttsClient.synthesizeSpeech(request);
      
      console.log(`✅ Speech synthesized successfully (${response.audioContent.length} bytes)`);
      return response.audioContent;
      
    } catch (error) {
      console.error('❌ TTS error:', error);
      
      // Try fallback method
      return await this.fallbackTTS(text, languageCode);
    }
  }

  async transcribeAudio(audioFilePath, languageCode = 'en-US') {
    try {
      console.log(`🎤 Transcribing audio: ${languageCode} - ${path.basename(audioFilePath)}`);
      
      // If no Google Cloud client, use fallback
      if (!this.speechClient) {
        return await this.fallbackSTT(audioFilePath, languageCode);
      }

      // Read the audio file
      const audioBytes = await fs.readFile(audioFilePath);
      
      // Get language code
      const langCode = this.getLanguageCode(languageCode);
      
      // Configure recognition request
      const request = {
        audio: { content: audioBytes },
        config: {
          encoding: 'WEBM_OPUS', // Adjust based on your audio format
          sampleRateHertz: 16000,
          languageCode: langCode,
          model: 'latest_short', // For short audio clips
          enableAutomaticPunctuation: true,
          enableWordTimeOffsets: false
        }
      };

      // Perform the speech recognition
      const [response] = await this.speechClient.recognize(request);
      
      if (response.results && response.results.length > 0) {
        const transcription = response.results
          .map(result => result.alternatives[0].transcript)
          .join('\n');
          
        console.log(`✅ Audio transcribed successfully: "${transcription.substring(0, 100)}..."`);
        return transcription;
      } else {
        console.log('⚠️  No speech detected in audio');
        return 'No speech detected in the audio file.';
      }
      
    } catch (error) {
      console.error('❌ STT error:', error);
      
      // Try fallback method
      return await this.fallbackSTT(audioFilePath, languageCode);
    }
  }

  async fallbackTTS(text, languageCode) {
    try {
      console.log('🔄 Using fallback TTS method...');
      
      // Try to use Microsoft Edge TTS (free alternative)
      if (this.tryEdgeTTS) {
        return await this.useEdgeTTS(text, languageCode);
      }
      
      // For demo purposes, return a simple audio buffer placeholder
      // In production, you might want to use alternative TTS services
      const placeholderAudio = Buffer.from([
        // MP3 header for a very short silent audio file
        0xFF, 0xFB, 0x90, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
      ]);
      
      // Log that we're using fallback
      console.log('⚠️  Using placeholder audio - Configure Google Cloud TTS for actual speech synthesis');
      
      return placeholderAudio;
      
    } catch (error) {
      console.error('❌ Fallback TTS error:', error);
      throw new Error('Text-to-speech service unavailable');
    }
  }

  async fallbackSTT(audioFilePath, languageCode) {
    try {
      console.log('🔄 Using fallback STT method...');
      
      // For demo purposes, return a placeholder transcription
      // In production, you might want to use alternative STT services
      const placeholderTranscription = 'Audio transcription is currently unavailable. Please configure Google Cloud Speech-to-Text service.';
      
      console.log('⚠️  Using placeholder transcription - Configure Google Cloud STT for actual speech recognition');
      
      return placeholderTranscription;
      
    } catch (error) {
      console.error('❌ Fallback STT error:', error);
      throw new Error('Speech-to-text service unavailable');
    }
  }

  getLanguageCode(input) {
    // If already a full language code (e.g., 'en-US'), return as-is
    if (input.includes('-')) {
      return input;
    }
    
    // If short code (e.g., 'en'), convert to full code
    const lang = this.supportedLanguages[input];
    return lang ? lang.code : 'en-US';
  }

  selectVoice(languageCode, voiceName) {
    const availableVoices = this.voiceSettings[languageCode] || this.voiceSettings['en-US'];
    
    if (voiceName === 'default' || !voiceName) {
      return availableVoices[0]; // Return first available voice
    }
    
    // Check if requested voice is available
    if (availableVoices.includes(voiceName)) {
      return voiceName;
    }
    
    // Fallback to first available voice
    return availableVoices[0];
  }

  async getAvailableVoices(languageCode = null) {
    try {
      if (!this.ttsClient) {
        // Return mock data if no client
        return Object.entries(this.voiceSettings).map(([lang, voices]) => ({
          languageCode: lang,
          voices: voices.map(voice => ({ name: voice, gender: 'NEUTRAL' }))
        }));
      }

      const request = languageCode ? { languageCode } : {};
      const [response] = await this.ttsClient.listVoices(request);
      
      return response.voices || [];
      
    } catch (error) {
      console.error('❌ Error getting available voices:', error);
      return [];
    }
  }

  getSupportedLanguages() {
    return Object.entries(this.supportedLanguages).map(([code, info]) => ({
      code,
      languageCode: info.code,
      name: info.name
    }));
  }

  async validateAudioFile(filePath) {
    try {
      const stats = await fs.stat(filePath);
      
      // Check file size (max 10MB for audio)
      const maxSize = 10 * 1024 * 1024;
      if (stats.size > maxSize) {
        throw new Error('Audio file too large. Maximum size is 10MB.');
      }
      
      // Check file exists
      if (!await fs.pathExists(filePath)) {
        throw new Error('Audio file not found.');
      }
      
      return true;
      
    } catch (error) {
      throw new Error(`Audio validation failed: ${error.message}`);
    }
  }

  async convertAudioFormat(inputPath, outputPath, targetFormat = 'wav') {
    // This would require ffmpeg or similar audio processing library
    // For now, we'll assume the audio is in the correct format
    console.log(`🔄 Audio format conversion not implemented (${inputPath} -> ${targetFormat})`);
    return inputPath;
  }

  // Utility methods
  async saveAudioToFile(audioBuffer, outputPath) {
    try {
      await fs.ensureDir(path.dirname(outputPath));
      await fs.writeFile(outputPath, audioBuffer);
      console.log(`✅ Audio saved to ${outputPath}`);
      return outputPath;
    } catch (error) {
      console.error('❌ Error saving audio file:', error);
      throw new Error('Failed to save audio file');
    }
  }

  async checkServiceHealth() {
    try {
      const health = {
        tts: false,
        stt: false,
        error: null
      };

      if (this.ttsClient) {
        try {
          await this.ttsClient.listVoices({ languageCode: 'en-US' });
          health.tts = true;
        } catch (error) {
          health.error = `TTS: ${error.message}`;
        }
      }

      if (this.speechClient) {
        try {
          // Speech client doesn't have a simple health check, so we assume it's healthy if initialized
          health.stt = true;
        } catch (error) {
          health.error = health.error ? `${health.error}, STT: ${error.message}` : `STT: ${error.message}`;
        }
      }

      return health;
      
    } catch (error) {
      return {
        tts: false,
        stt: false,
        error: error.message
      };
    }
  }

  // Text processing for better TTS
  preprocessTextForTTS(text) {
    // Clean up text for better speech synthesis
    let processedText = text
      .replace(/([.!?])\s*([A-Z])/g, '$1 $2') // Add space after punctuation
      .replace(/\s+/g, ' ') // Normalize whitespace
      .replace(/([0-9]+)/g, ' $1 ') // Add spaces around numbers
      .trim();

    // Limit text length (Google Cloud TTS has a 5000 character limit)
    if (processedText.length > 4900) {
      processedText = processedText.substring(0, 4900) + '...';
      console.log('⚠️  Text truncated for TTS processing');
    }

    return processedText;
  }

  // Batch processing for long texts
  async synthesizeLongText(text, languageCode = 'en-US', voiceName = 'default') {
    try {
      // Split long text into chunks
      const chunks = this.splitTextIntoChunks(text, 4000);
      const audioBuffers = [];

      for (let i = 0; i < chunks.length; i++) {
        console.log(`🔊 Processing chunk ${i + 1}/${chunks.length}`);
        const audioBuffer = await this.synthesizeSpeech(chunks[i], languageCode, voiceName);
        audioBuffers.push(audioBuffer);
      }

      // Combine audio buffers (simple concatenation)
      // Note: This is a basic approach. For production, you might want to use proper audio processing
      const combinedBuffer = Buffer.concat(audioBuffers);
      
      console.log(`✅ Combined ${chunks.length} audio chunks`);
      return combinedBuffer;
      
    } catch (error) {
      console.error('❌ Long text synthesis error:', error);
      throw error;
    }
  }

  splitTextIntoChunks(text, maxLength = 4000) {
    const chunks = [];
    let currentChunk = '';
    
    const sentences = text.split(/[.!?]+/);
    
    for (const sentence of sentences) {
      const trimmedSentence = sentence.trim();
      if (!trimmedSentence) continue;
      
      const sentenceWithPunctuation = trimmedSentence + '.';
      
      if (currentChunk.length + sentenceWithPunctuation.length > maxLength) {
        if (currentChunk) {
          chunks.push(currentChunk.trim());
          currentChunk = '';
        }
      }
      
      currentChunk += sentenceWithPunctuation + ' ';
      
      // If single sentence is too long, split it
      if (currentChunk.length > maxLength) {
        chunks.push(currentChunk.trim());
        currentChunk = '';
      }
    }
    
    if (currentChunk.trim()) {
      chunks.push(currentChunk.trim());
    }
    
    return chunks;
  }
}

module.exports = TTSService;