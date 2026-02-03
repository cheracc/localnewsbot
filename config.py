import os
import sys
from typing import Dict, Any, Optional
import yaml

class Config:
    """
    Configuration handler for reading config.yml
    """

    def read_config(self, path: str) -> Dict[str, Any]:
        """
        Read config.yml and return its contents as a dict.
        If path is None, looks for config.yml in the same directory as this file.
        Returns an empty dict if the file does not exist.
        """
        if path is None:
            path = os.path.join(os.path.dirname(__file__), "config.yml")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}

        if not isinstance(data, dict):
            raise ValueError(f"{path} does not contain a YAML mapping at top level")

        return data

    def __init__(self):
        self.config = self.read_config("config.yml")

        if 'bsky_handle' not in self.config or 'bsky_password' not in self.config:
            print("config.yml must contain 'bsky_handle' and 'bsky_password' keys")
            sys.exit(1)
        
        self.handle = self.config['bsky_handle']
        self.password = self.config['bsky_password']
        self.max_articles_per_feed = self.config['max_articles_per_feed']

    def get_rss_feeds(self) -> Dict[str, Any]:
        feeds = self.config.get("rss_feeds", {}) or {}
        if not isinstance(feeds, dict):
            raise ValueError("rss_feeds in config must be a mapping")
        return feeds
    
    def get_html_sources(self) -> Dict[str, Any]:
        sources = self.config.get("html_sources", {}) or {}
        if not isinstance(sources, dict):
            raise ValueError("html_sources in config must be a mapping")
        return sources
    
    def get_bad_words(self) -> list[str]:
        bad_words = self.config.get("bad_words", []) or []
        if not isinstance(bad_words, list):
            raise ValueError("bad_words in config must be a list")
        return bad_words
    
    def get_good_words(self) -> list[str]:
        good_words = self.config.get("good_words", []) or []
        if not isinstance(good_words, list):
            raise ValueError("good_words in config must be a list")
        return good_words