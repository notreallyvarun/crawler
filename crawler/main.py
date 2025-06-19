import logging
import json
import sys  
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from config import Config
from crawler.utils.pdf_processor import PDFProcessor
from crawler.utils.azure_llm_client import AzureLLMClient
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

class KamcoPDFSummarizer:
    def __init__(self):
        self.config = Config()
        self.pdf_processor = PDFProcessor(max_chars=self.config.MAX_CHARS_PER_PAGE)
        self.llm_client = AzureLLMClient()
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.config.LOGS_FOLDER / f"summarizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("PDF Summarizer initialized")
    
    def find_latest_pdf(self) -> Path:
        """Find the most recently downloaded PDF"""
        pdf_files = list(self.config.PDF_FOLDER.glob("*.pdf"))
        
        if not pdf_files:
            raise FileNotFoundError(f"No PDF files found in {self.config.PDF_FOLDER}")
        
        # Sort by modification time (newest first)
        latest_pdf = max(pdf_files, key=lambda p: p.stat().st_mtime)
        self.logger.info(f"Latest PDF found: {latest_pdf.name}")
        return latest_pdf
    
    def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Process a single PDF file"""
        self.logger.info(f"Processing PDF: {pdf_path.name}")
        
        result = {
            'filename': pdf_path.name,
            'file_path': str(pdf_path),
            'processed_at': datetime.now().isoformat(),
            'success': False,
            'error': None,
            'metadata': {},
            'summary': {}
        }
        
        try:
            # Extract PDF metadata
            result['metadata'] = self.pdf_processor.get_pdf_metadata(str(pdf_path))
            self.logger.info(f"PDF metadata extracted: {result['metadata']['pages']} pages")
            
            # Extract text from first page
            text = self.pdf_processor.extract_first_page_text(str(pdf_path))
            
            if not text:
                result['error'] = "No text extracted from first page"
                self.logger.warning(f"No text extracted from {pdf_path.name}")
                return result
            
            self.logger.info(f"Text extracted: {len(text)} characters")
            
            # Summarize using Azure OpenAI
            summary = self.llm_client.summarize_text(text, "Kuwait financial report")
            
            if not summary:
                result['error'] = "Failed to generate summary"
                self.logger.error(f"Failed to generate summary for {pdf_path.name}")
                return result
            
            result['summary'] = summary
            result['success'] = True
            
            self.logger.info(f"Successfully processed {pdf_path.name}")
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Error processing {pdf_path.name}: {str(e)}")
        
        return result
    
    def save_summary(self, result: Dict[str, Any]) -> Path:
        """Save summary to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_{Path(result['filename']).stem}_{timestamp}.json"
        summary_path = self.config.SUMMARIES_FOLDER / filename
        
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Summary saved to: {summary_path}")
            return summary_path
            
        except Exception as e:
            self.logger.error(f"Failed to save summary: {str(e)}")
            raise
    
    def run(self, pdf_path: str = None) -> Dict[str, Any]: # type: ignore
        self.logger.info("Starting PDF summarization process")
        
        try:
            # Find PDF to process
            if pdf_path:
                pdf_file = Path(pdf_path)
                if not pdf_file.exists():
                    raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            else:
                pdf_file = self.find_latest_pdf()
            
            # Process the PDF
            result = self.process_pdf(pdf_file)
            
            # Save summary
            if result['success']:
                summary_path = self.save_summary(result)
                result['summary_file'] = str(summary_path)
                
                # Print summary to console
                self.print_summary(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Fatal error in summarization process: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processed_at': datetime.now().isoformat()
            }
    
    def print_summary(self, result: Dict[str, Any]):
        print("\n" + "="*60)
        print("PDF SUMMARY")
        print("="*60)
        print(f"File: {result['filename']}")
        print("-"*60)
        
        if result['success'] and result['summary']:
            summary = result['summary']
            
            print(f"SUMMARY:")
            print(f"{summary.get('Summary', 'N/A')}\n")
            
            
def main():
    try:
        summarizer = KamcoPDFSummarizer()
        result = summarizer.run()
        
        if result['success']:
            print(f"\n✅ PDF summarization completed successfully!")
            print(f"Summary saved to: {result.get('summary_file', 'Unknown')}")
        else:
            print(f"\n❌ PDF summarization failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")

if __name__ == "__main__":
    main()