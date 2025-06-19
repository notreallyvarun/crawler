import openai
import logging
import time
from typing import Optional, Dict, Any
from config import Config

class AzureLLMClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        self.config.validate_config()
        
        # Initialize Azure OpenAI client
        self.client = openai.AzureOpenAI(
            api_key=self.config.AZURE_OPENAI_API_KEY,
            api_version=self.config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=self.config.AZURE_OPENAI_ENDPOINT  # type: ignore
        )
        
        self.logger.info("Azure OpenAI client initialized successfully")
    
    def summarize_text(self, text: str, document_type: str = "financial report") -> Optional[Dict[str, Any]]:
        """Summarize text using Azure OpenAI"""
        if not text or text.strip() == "":
            self.logger.warning("Empty text provided for summarization")
            return None
        
        try:
            # Create the prompt
            prompt = self._create_summary_prompt(text, document_type)
            
            # Try with primary deployment first
            response = self._make_api_call(prompt, self.config.AZURE_OPENAI_DEPLOYMENT_NAME)  # type: ignore
            
            if response is None and self.config.AZURE_OPENAI_DEPLOYMENT_NAME_35:  # type: ignore
                self.logger.info("Trying backup deployment...")
                response = self._make_api_call(prompt, self.config.AZURE_OPENAI_DEPLOYMENT_NAME_35)  # type: ignore
            
            if response is None:
                self.logger.error("Failed to get response from Azure OpenAI")
                return None
            
            # Parse the response (just wrap raw text in dict)
            return self._parse_response(response)
            
        except Exception as e:
            self.logger.error(f"Error in summarize_text: {str(e)}")
            return None
    
    def _create_summary_prompt(self, text: str, document_type: str) -> str:
        prompt = f"""

{text}
**TASKS**
Summarize the summary data in the following way:-
1. Summary must be revolving around Boursa Kuwait Market.
2. Identify key numerical values and shares associated with them.
 . Analyze the data summary created from the above steps to write a shorter, more concise summary the will be around 300 characters long
**IMPORTANT**
1. Check whether the data in the summary matches the initial data at each iteration.
2. Use comparative language, i.e. comparing tone
3. Do not predict or make up any information.
4. Make it short, concise and human readable.
5. Use formal and professional language, i.e. like a journalist
6. Use only DTD numerics as the parameters. 
7. Style the summary like BBC 
**OUTPUT**
must be in form of simple english, forming proper sentences.
"""
        return prompt.strip()
    
    def _make_api_call(self, prompt: str, deployment_name: str) -> Optional[str]:
        for attempt in range(self.config.MAX_RETRIES):
            try:
                self.logger.info(f"Making API call to {deployment_name} (attempt {attempt + 1})")
                
                response = self.client.chat.completions.create(
                    model=deployment_name,
                    messages=[
                        {"role": "system", "content": "You are an expert financial journalist who provides clear, structured, and brief summaries."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.3,
                )
                
                if response.choices and response.choices[0].message:
                    content = response.choices[0].message.content
                    self.logger.info("Successfully received response from Azure OpenAI")
                    return content
                else:
                    self.logger.warning("Empty response from Azure OpenAI")
                    return None
                    
            except openai.RateLimitError as e:
                self.logger.warning(f"Rate limit exceeded (attempt {attempt + 1}): {str(e)}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(self.config.RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                continue
                
            except openai.APITimeoutError as e:
                self.logger.warning(f"API timeout (attempt {attempt + 1}): {str(e)}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(self.config.RETRY_DELAY)
                continue
                
            except Exception as e:
                self.logger.error(f"API call failed (attempt {attempt + 1}): {str(e)}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(self.config.RETRY_DELAY)
                continue
        
        return None
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        # Return raw summary text inside a dict
        return {'Summary': response.strip()}
