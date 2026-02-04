import os
import sys
from typing import Dict, Any, Optional
import yaml

# Config handles reading and providing access to configuration settings from config.yml
class Config:

    def __init__(self):
        self.config = self.read_config("config.yml")

        if 'bsky_handle' not in self.config or 'bsky_password' not in self.config:
            print("config.yml must contain 'bsky_handle' and 'bsky_password' keys")
            sys.exit(1)
        
        self.handle = self.config['bsky_handle']
        self.password = self.config['bsky_password']
        self.max_articles_per_feed = self.config['max_articles_per_feed']

    def read_config(self, path: str) -> Dict[str, Any]:
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

    # Returns the RSS feeds from config
    def get_rss_feeds(self) -> Dict[str, Any]:
        feeds = self.config.get("rss_feeds", {}) or {}
        if not isinstance(feeds, dict):
            raise ValueError("rss_feeds in config must be a mapping")
        return feeds
    
    # Returns the HTML sources from config
    def get_html_sources(self) -> Dict[str, Any]:
        sources = self.config.get("html_sources", {}) or {}
        if not isinstance(sources, dict):
            raise ValueError("html_sources in config must be a mapping")
        return sources
    
    # Returns the list of bad words from config
    def get_bad_words(self) -> list[str]:
        bad_words = self.config.get("bad_words", []) or []
        if not isinstance(bad_words, list):
            raise ValueError("bad_words in config must be a list")
        return bad_words
    
    # Returns the list of good words from config
    def get_good_words(self) -> list[str]:
        good_words = self.config.get("good_words", []) or []
        if not isinstance(good_words, list):
            raise ValueError("good_words in config must be a list")
        return good_words
    
    # Returns the log level from config
    def get_log_level(self) -> str:
        log_level = self.config.get("log_level", "INFO")
        if not isinstance(log_level, str):
            raise ValueError("log_level in config must be a string")
        return log_level