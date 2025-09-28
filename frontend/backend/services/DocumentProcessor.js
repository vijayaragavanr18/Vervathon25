const pdf = require('pdf-parse');
const mammoth = require('mammoth');
const XLSX = require('xlsx');
const fs = require('fs-extra');
const path = require('path');

class DocumentProcessor {
  constructor() {
    this.supportedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];
  }

  async extractText(filePath, mimeType) {
    try {
      console.log(`📄 Extracting text from ${path.basename(filePath)} (${mimeType})`);
      
      if (!this.supportedTypes.includes(mimeType)) {
        throw new Error(`Unsupported file type: ${mimeType}`);
      }

      let extractedText = '';

      switch (mimeType) {
        case 'application/pdf':
          extractedText = await this.extractFromPDF(filePath);
          break;
        
        case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
          extractedText = await this.extractFromDocx(filePath);
          break;
        
        case 'text/plain':
          extractedText = await this.extractFromTxt(filePath);
          break;
        
        case 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
          extractedText = await this.extractFromExcel(filePath);
          break;
        
        case 'application/vnd.openxmlformats-officedocument.presentationml.presentation':
          extractedText = await this.extractFromPowerPoint(filePath);
          break;
        
        default:
          throw new Error(`Handler not implemented for ${mimeType}`);
      }

      // Clean and validate extracted text
      extractedText = this.cleanText(extractedText);
      
      if (!extractedText || extractedText.trim().length === 0) {
        throw new Error('No text could be extracted from the document');
      }

      console.log(`✅ Extracted ${extractedText.length} characters from ${path.basename(filePath)}`);
      return extractedText;

    } catch (error) {
      console.error(`❌ Error extracting text from ${filePath}:`, error);
      throw new Error(`Text extraction failed: ${error.message}`);
    }
  }

  async extractFromPDF(filePath) {
    try {
      const dataBuffer = await fs.readFile(filePath);
      const pdfData = await pdf(dataBuffer);
      return pdfData.text;
    } catch (error) {
      throw new Error(`PDF extraction failed: ${error.message}`);
    }
  }

  async extractFromDocx(filePath) {
    try {
      const result = await mammoth.extractRawText({ path: filePath });
      return result.value;
    } catch (error) {
      throw new Error(`DOCX extraction failed: ${error.message}`);
    }
  }

  async extractFromTxt(filePath) {
    try {
      const text = await fs.readFile(filePath, 'utf8');
      return text;
    } catch (error) {
      throw new Error(`TXT extraction failed: ${error.message}`);
    }
  }

  async extractFromExcel(filePath) {
    try {
      const workbook = XLSX.readFile(filePath);
      let allText = '';
      
      workbook.SheetNames.forEach(sheetName => {
        const worksheet = workbook.Sheets[sheetName];
        const sheetData = XLSX.utils.sheet_to_csv(worksheet);
        allText += `Sheet: ${sheetName}\n${sheetData}\n\n`;
      });
      
      return allText;
    } catch (error) {
      throw new Error(`Excel extraction failed: ${error.message}`);
    }
  }

  async extractFromPowerPoint(filePath) {
    try {
      // For PowerPoint, we'll use a simpler approach
      // In production, you might want to use a more sophisticated library
      const { execSync } = require('child_process');
      
      // Try to use LibreOffice if available (optional)
      try {
        const tempTxt = filePath + '.txt';
        execSync(`soffice --headless --invisible --convert-to txt --outdir "${path.dirname(filePath)}" "${filePath}"`);
        
        if (await fs.pathExists(tempTxt)) {
          const text = await fs.readFile(tempTxt, 'utf8');
          await fs.unlink(tempTxt); // Clean up
          return text;
        }
      } catch (libreOfficeError) {
        // LibreOffice not available, return placeholder
        console.warn('LibreOffice not available for PowerPoint processing');
      }
      
      // Fallback: return basic info
      return `PowerPoint file processed: ${path.basename(filePath)}. Content extraction requires LibreOffice for full text extraction.`;
      
    } catch (error) {
      throw new Error(`PowerPoint extraction failed: ${error.message}`);
    }
  }

  cleanText(text) {
    if (!text) return '';
    
    // Remove excessive whitespace
    text = text.replace(/\s+/g, ' ');
    
    // Remove special characters that might cause issues
    text = text.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
    
    // Trim whitespace
    text = text.trim();
    
    return text;
  }

  async getDocumentMetadata(filePath) {
    try {
      const stats = await fs.stat(filePath);
      const extension = path.extname(filePath).toLowerCase();
      
      return {
        fileName: path.basename(filePath),
        filePath: filePath,
        fileSize: stats.size,
        extension: extension,
        created: stats.birthtime,
        modified: stats.mtime,
        isSupported: this.supportedTypes.some(type => 
          this.getExtensionFromMimeType(type) === extension
        )
      };
    } catch (error) {
      throw new Error(`Failed to get document metadata: ${error.message}`);
    }
  }

  getExtensionFromMimeType(mimeType) {
    const mimeToExt = {
      'application/pdf': '.pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
      'text/plain': '.txt',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx'
    };
    
    return mimeToExt[mimeType] || '';
  }

  async validateDocument(filePath, mimeType) {
    try {
      // Check if file exists
      if (!await fs.pathExists(filePath)) {
        throw new Error('File does not exist');
      }
      
      // Check file size (limit: 10MB)
      const stats = await fs.stat(filePath);
      const maxSize = parseInt(process.env.MAX_FILE_SIZE) || 10 * 1024 * 1024;
      
      if (stats.size > maxSize) {
        throw new Error(`File too large. Maximum size is ${maxSize / 1024 / 1024}MB`);
      }
      
      // Check if mime type is supported
      if (!this.supportedTypes.includes(mimeType)) {
        throw new Error(`Unsupported file type: ${mimeType}`);
      }
      
      // Basic file integrity check
      const buffer = await fs.readFile(filePath, { start: 0, end: 10 });
      if (buffer.length === 0) {
        throw new Error('File appears to be empty or corrupted');
      }
      
      return true;
      
    } catch (error) {
      throw new Error(`Document validation failed: ${error.message}`);
    }
  }

  async processMultipleDocuments(filePaths) {
    const results = [];
    
    for (const filePath of filePaths) {
      try {
        const metadata = await this.getDocumentMetadata(filePath);
        const mimeType = this.getMimeTypeFromExtension(metadata.extension);
        
        if (mimeType) {
          await this.validateDocument(filePath, mimeType);
          const text = await this.extractText(filePath, mimeType);
          
          results.push({
            ...metadata,
            mimeType,
            extractedText: text,
            success: true
          });
        } else {
          results.push({
            ...metadata,
            success: false,
            error: 'Unsupported file type'
          });
        }
      } catch (error) {
        results.push({
          filePath,
          success: false,
          error: error.message
        });
      }
    }
    
    return results;
  }

  getMimeTypeFromExtension(extension) {
    const extToMime = {
      '.pdf': 'application/pdf',
      '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      '.txt': 'text/plain',
      '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    };
    
    return extToMime[extension.toLowerCase()] || null;
  }

  // Utility method to get a preview of the document content
  getTextPreview(text, maxLength = 500) {
    if (!text) return '';
    
    if (text.length <= maxLength) return text;
    
    const preview = text.substring(0, maxLength);
    const lastSpace = preview.lastIndexOf(' ');
    
    return lastSpace > 0 ? preview.substring(0, lastSpace) + '...' : preview + '...';
  }

  // Count words in extracted text
  getWordCount(text) {
    if (!text) return 0;
    return text.trim().split(/\s+/).length;
  }

  // Get reading time estimate (average reading speed: 200 words per minute)
  getReadingTime(text) {
    const wordCount = this.getWordCount(text);
    const minutes = Math.ceil(wordCount / 200);
    return minutes;
  }

  // Extract key information from text
  extractKeyInfo(text) {
    const info = {
      wordCount: this.getWordCount(text),
      readingTime: this.getReadingTime(text),
      preview: this.getTextPreview(text),
      isEmpty: !text || text.trim().length === 0
    };
    
    return info;
  }
}

module.exports = DocumentProcessor;