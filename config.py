import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    AZURE_OPENAI_MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4")
    
   
    BASE_DIR = Path(__file__).parent
    PDF_FOLDER = BASE_DIR / "kamco_reports"
    SUMMARIES_FOLDER = BASE_DIR / "summaries"
    LOGS_FOLDER = BASE_DIR / "logs"
    
    PDF_FOLDER.mkdir(exist_ok=True)
    SUMMARIES_FOLDER.mkdir(exist_ok=True)
    LOGS_FOLDER.mkdir(exist_ok=True)
    
    MAX_PAGES_TO_PROCESS = 1  
    MAX_CHARS_PER_PAGE = 4000  
    
    MAX_RETRIES = 3
    RETRY_DELAY = 1 
    
    @classmethod
    def validate_config(cls):
        
        required_vars = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT", 
            "AZURE_OPENAI_DEPLOYMENT_NAME"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True