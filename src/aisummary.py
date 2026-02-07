from __future__ import annotations
from google import genai
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.config import Config


# Summarizer uses google GenAI to summarize a news article
class Summarizer:
    def __init__(self, config: Config): 
        self.client = genai.Client(api_key=config.get_gemini_api_key())
        self.logger = config.get_logger()
        self.prompt = config.get_ai_summary_prompt()
        self.model = config.get_gemini_model()
        

    def summarize(self, link_to_article: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=self.prompt + link_to_article,
            )
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return ""

        return response.text if response and response.text else ""
    
