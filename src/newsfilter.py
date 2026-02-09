from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bsky_post import BskyPost
    from src.config import Config


class NewsFilter(ABC):
    """Abstract base class for news filtering implementations."""
    
    def __init__(self, config: Config):
        self.data = config.db
        self.config = config
        self.logger = config.get_logger()
    
    @abstractmethod
    def filter(self, articles: list[BskyPost]) -> list[BskyPost]:
        """
        Filter a list of articles and return the filtered list.
        
        Args:
            articles: List of BskyPost articles to filter
            
        Returns:
            List of articles that passed the filter
        """
        pass