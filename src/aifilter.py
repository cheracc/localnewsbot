from __future__ import annotations
from typing import TYPE_CHECKING
from src.newsfilter import NewsFilter
from google import genai
if TYPE_CHECKING:
    from bsky_post import BskyPost
    from src.config import Config


# AIFilter uses Google Gemini API to score article quality and relevance
class AIFilter(NewsFilter):
    def __init__(self, config: Config):
        super().__init__(config)
        self.client: genai.Client | None = None
        self.enabled = False
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Gemini API client for quality scoring."""
        api_key = self.config.get_gemini_api_key()
        
        if not api_key or api_key == "your-api-key-here":
            self.logger.warning("Gemini API key not configured. AI filtering disabled.")
            return
        
        try:
            self.client = genai.Client(api_key=api_key)
            # Test the API key with a simple call
            self.client.models.list()
            self.enabled = True
            self.logger.info("   Gemini API initialized successfully. AI filtering enabled.")
        except Exception as e:
            self.logger.warning(f"Error initializing Gemini API for filtering: {e}. AI filtering disabled.")
    
    def filter(self, articles: list[BskyPost]) -> list[BskyPost]:
        """
        Filter articles using AI quality scoring.
        
        Articles are scored 0-1 where:
        - 1.0 = high quality, relevant local news
        - 0.5 = borderline quality
        - 0.0 = low quality, spam, not relevant
        
        Articles scoring above the quality threshold are kept.
        """
        if not self.enabled:
            self.logger.warning("AI filter is disabled. Returning all articles unfiltered.")
            return articles
        
        # First, filter out duplicates and previously posted/excluded
        previously_posted = []
        for art in articles:
            if self.data.has_posted_article(art.link):
                previously_posted.append(art)

        previously_excluded = []
        for art in articles:
            if self.data.is_excluded(art.link):
                previously_excluded.append(art)

        to_remove = previously_excluded + previously_posted
        working_articles = [art for art in articles if art not in to_remove]
        
        self.logger.debug(f"Removed {len(previously_posted)} articles that were already posted and {len(previously_excluded)} articles that were previously excluded")
        
        # Score articles using AI
        quality_threshold = self.config.get_ai_filter_quality_threshold()
        scored_articles = []
        removed_articles = []
        
        for article in working_articles:
            score = self._score_article(article)
            if score >= quality_threshold:
                self.logger.debug(f"Article passed AI filter (score: {score:.2f}): {article.headline}")
                scored_articles.append(article)
            else:
                self.logger.debug(f"Article failed AI filter (score: {score:.2f}): {article.headline}")
                removed_articles.append(article)
                self.data.record_excluded_article(article.link)
        
        self.logger.info(f"AI filter results: {len(scored_articles)} articles kept, {len(removed_articles)} articles excluded")
        if removed_articles:
            self.logger.info(" The following articles were removed by AI filter:")
            for article in removed_articles:
                self.logger.info(f"   -  {article.headline}({article.source_name})")
        
        return scored_articles
    
    def _score_article(self, article: BskyPost) -> float:
        """
        Score an article's quality and relevance (0.0-1.0).
        
        Returns a score between 0 and 1, where 1 is high quality local news.
        Returns 0.5 on error to allow the article through (fail-safe).
        """
        if not self.enabled or self.client is None:
            return 0.5
        
        try:
            prompt = f"""Rate the quality and relevance of this local news article on a scale of 0 to 1.
            
Consider:
- Is this relevant to the local community of South Central Pennsylvania?
- Is the content factual and well-written?
- Is this newsworthy (not spam or clickbait)?
- Would a local news reader find this interesting?

Score Poorly If:
- The article involves another country or region with no local angle.
- The article is about national politics, celebrity gossip, or weather from another area.
- The article is an opinion piece or letter to the editor.
- The article is clickbait, sensationalized, or has misleading headlines.
- The article is about national sports, unless it has a strong local angle (e.g., local player)

Scoring guide:
0.0-0.3: Low quality, spam, not newsworthy
0.3-0.6: Borderline - may be relevant but low quality
0.6-0.8: Good quality local news
0.8-1.0: High quality, timely, highly relevant local news

Article:
Headline: {article.headline}
Description: {article.description[:500]}

Response: Provide ONLY a decimal number between 0 and 1 (e.g., 0.75). No explanation needed."""

            response = self.client.models.generate_content(
                model=self.config.get_gemini_model(),
                contents=prompt
            )
            
            if response and response.text:
                try:
                    score = float(response.text.strip())
                    # Clamp to 0-1 range
                    return max(0.0, min(1.0, score))
                except ValueError:
                    self.logger.warning(f"Could not parse AI score response: {response.text}")
                    return 0.5
            else:
                self.logger.warning("Empty response from AI quality scorer")
                return 0.5
                
        except Exception as e:
            self.logger.error(f"Error scoring article '{article.headline}': {e}")
            return 0.5
