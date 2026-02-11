from __future__ import annotations
from google import genai
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.config import Config
    from src.bsky_post import BskyPost


# Summarizer uses google GenAI to summarize a news article
class Summarizer:
    def __init__(self, config: Config):
        """Initialize Summarizer with Gemini API. Disables if API key is not configured."""
        self.config = config
        self.logger = config.get_logger()
        self.enabled = False
        
        api_key = config.get_gemini_api_key()
        
        # Check if API key exists and is not a placeholder
        if not self._is_api_key_valid(api_key):
            self.logger.warning("Gemini API key not configured. AI summarization disabled.")
            return
        
        try:
            self.client = genai.Client(api_key=api_key)
            # Test the API key with a simple call
            self.client.models.list()
            self.enabled = True
            self.logger.info("   Gemini API initialized successfully. AI summarization enabled.")
        except Exception as e:
            self.logger.warning(f"  Error initializing Gemini API: {e}. AI summarization disabled.")

    @staticmethod
    def _is_api_key_valid(api_key: str) -> bool:
        """Check if API key is configured and not a placeholder."""
        return bool(api_key and api_key.strip() and api_key != "your-api-key-here")

    def summarize(self, post: BskyPost) -> str:
        """Summarize an article using Gemini API. Returns empty string if disabled or on error."""
        if not self.enabled:
            return ""
        
        try:
            article_content = f"Headline: {post.headline}\n\nDescription: {post.description}"
            response = self.client.models.generate_content(
                model=self.config.get_gemini_model(),
                contents=self.config.get_ai_summary_prompt() + article_content,
            )
            return response.text if response and response.text else ""
        except Exception as e:
            self.logger.error(f"Error generating summary for {post.headline}: {e}")
            return ""
    
    def is_enabled(self) -> bool:
        """Return whether AI summarization is enabled."""
        return self.enabled

