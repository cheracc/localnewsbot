from __future__ import annotations
from google import genai
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.config import Config


# Summarizer uses google GenAI to summarize a news article
class Summarizer:
    def __init__(self, config: Config): 
        self.config = config
        self.logger = config.get_logger()
        self.prompt = config.get_ai_summary_prompt()
        self.model = config.get_gemini_model()
        self.enabled = False
        
        api_key = config.get_gemini_api_key()
        
        # Check if API key exists and is not a placeholder
        if not api_key or api_key.strip() == "" or api_key == "your-api-key-here":
            self.logger.warning("Gemini API key not configured. AI summarization disabled.")
            return
        
        try:
            self.client = genai.Client(api_key=api_key)
            # Test the API key with a simple call
            self.client.models.list()
            self.enabled = True
            self.logger.info("Gemini API initialized successfully. AI summarization enabled.")
        except Exception as e:
            self.logger.warning(f"Error initializing Gemini API: {e}. AI summarization disabled.")

    def summarize(self, link_to_article: str) -> str:
        """Summarize an article using Gemini API. Returns empty string if disabled or on error."""
        if not self.enabled:
            return ""
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=self.prompt + link_to_article,
            )
            return response.text if response and response.text else ""
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return ""
    
    def is_enabled(self) -> bool:
        """Return whether AI summarization is enabled."""
        return self.enabled

