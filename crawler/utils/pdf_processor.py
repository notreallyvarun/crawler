import PyPDF2
import logging
from pathlib import Path
from typing import Optional, List, Dict
import re

class PDFProcessor:
    def __init__(self, max_chars: int = 4000):
        self.max_chars = max_chars
        self.logger = logging.getLogger(__name__)
    
    def extract_first_page_text(self, pdf_path: str) -> Optional[str]:
        """Extract text from the first page of a PDF"""
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                self.logger.error(f"PDF file not found: {pdf_path}")
                return None
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if len(pdf_reader.pages) == 0:
                    self.logger.warning(f"PDF has no pages: {pdf_path}")
                    return None
                
                # Extract text from first page
                first_page = pdf_reader.pages[0]
                text = first_page.extract_text()
                
                if not text or text.strip() == "":
                    self.logger.warning(f"No text found on first page: {pdf_path}")
                    return None
                
                # Clean and limit text
                cleaned_text = self.clean_text(text)
                limited_text = self.limit_text_length(cleaned_text)
                
                self.logger.info(f"Extracted {len(limited_text)} characters from first page of {pdf_path.name}")
                return limited_text
                
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text by removing extra whitespace and special characters"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s\-.,;:!?()%$€£¥₹]', '', text)
        
        # Remove page numbers and common headers/footers
        text = re.sub(r'\b\d{1,3}\b(?=\s*$)', '', text)  # Remove trailing page numbers
        text = re.sub(r'^page\s+\d+', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def limit_text_length(self, text: str) -> str:
        """Limit text length to avoid API token limits"""
        if len(text) <= self.max_chars:
            return text
        
        # Try to cut at a sentence boundary
        truncated = text[:self.max_chars]
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')
        
        # Find the last sentence ending
        last_sentence_end = max(last_period, last_exclamation, last_question)
        
        if last_sentence_end > self.max_chars * 0.8:  # If we found a good cutoff point
            return truncated[:last_sentence_end + 1]
        else:
            # Cut at word boundary
            last_space = truncated.rfind(' ')
            if last_space > 0:
                return truncated[:last_space] + "..."
            else:
                return truncated + "..."
    
    def get_pdf_metadata(self, pdf_path: str) -> Dict:
        """Extract metadata from PDF"""
        try:
            pdf_path = Path(pdf_path)
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                metadata = {
                    'filename': pdf_path.name,
                    'pages': len(pdf_reader.pages),
                    'file_size': pdf_path.stat().st_size,
                    'title': '',
                    'author': '',
                    'subject': '',
                    'creator': ''
                }
                
                # Extract PDF metadata if available
                if pdf_reader.metadata:
                    metadata.update({
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', '')
                    })
                
                return metadata
                
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {pdf_path}: {str(e)}")
            return {'filename': Path(pdf_path).name, 'error': str(e)}