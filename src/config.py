import datetime
import os
import sys
from typing import Dict, Any, Optional
import yaml
import logging

# Config handles reading and providing access to configuration settings from config.yml
class Config:

    def __init__(self):
        self.__main_config = self.read_config("config/config.yml")
        self.logger = self.__create_logger()
        self.logger.debug("config.yml loaded successfully")
        self.__feed_config = self.read_config("config/feeds.yml")
        self.logger.debug("feeds.yml loaded successfully")
        self.__filter_config = self.read_config("config/filter.yml")
        self.logger.debug("filter.yml loaded successfully")
        self.__tags_config = self.read_config("config/tags.yml")
        self.logger.debug("tags.yml loaded successfully")


        if 'bsky_handle' not in self.__main_config or 'bsky_password' not in self.__main_config:
            self.logger.error("config.yml must contain 'bsky_handle' and 'bsky_password' keys")
            sys.exit(1)
        
        self.handle = self.__main_config['bsky_handle']
        self.password = self.__main_config['bsky_password']
        self.max_articles_per_feed = self.__main_config['max_articles_per_feed']

    def get_logger(self) -> logging.Logger:
        return self.logger

    def read_config(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except FileNotFoundError:
            self.logger.error(f"Config file {path} not found")
            sys.exit(1)

        if not isinstance(data, dict):
            sys.exit(1)
            raise ValueError(f"{path} does not contain a YAML mapping at top level")

        return data

    # Returns the RSS feeds from config
    def get_rss_feeds(self) -> Dict[str, Any]:
        feeds = self.__feed_config.get("rss_feeds", {}) or {}
        if not isinstance(feeds, dict):
            raise ValueError("rss_feeds in config must be a mapping")
        return feeds
    
    # Returns the HTML sources from config
    def get_html_sources(self) -> Dict[str, Any]:
        sources = self.__feed_config.get("html_sources", {}) or {}
        if not isinstance(sources, dict):
            raise ValueError("html_sources in config must be a mapping")
        return sources
    
    # Returns the list of bad words from config
    def get_bad_words(self) -> list[str]:
        bad_words = self.__filter_config.get("bad_words", []) or []
        if not isinstance(bad_words, list):
            raise ValueError("bad_words in config must be a list")
        return bad_words
    
    # Returns the list of good words from config
    def get_good_words(self) -> list[str]:
        good_words = self.__filter_config.get("good_words", []) or []
        if not isinstance(good_words, list):
            raise ValueError("good_words in config must be a list")
        return good_words
    
    # Returns the log level from config
    def get_log_level(self) -> str:
        log_level = self.__main_config.get("log_level", "INFO")
        if not isinstance(log_level, str):
            raise ValueError("log_level in config must be a string")
        return log_level
    
    def max_article_age_days(self) -> Optional[int]:
        max_age = self.__main_config.get("max_article_age_days", None)
        if max_age is not None:
            try:
                return int(max_age)
            except ValueError:
                raise ValueError("max_article_age_days in config must be an integer")
        return None
    
    def get_tags(self) -> Dict[str, str]:
        return self.__tags_config
    
    def __create_logger(self) -> logging.Logger:
        logger = logging.getLogger("bot")

        log_level_str = self.get_log_level().upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        logger.setLevel(log_level)

        os.makedirs("log", exist_ok=True)
        open(os.path.join("log", f"bot_{datetime.datetime.now().strftime('%Y%m%d')}.log"), "a").close()

        # File handler
        file_handler = logging.FileHandler(f"log/bot_{datetime.datetime.now().strftime('%Y%m%d')}.log")
        file_handler.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
