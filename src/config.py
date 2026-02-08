import datetime
import os
import sys

from src.aisummary import Summarizer
from src.data import DatabaseManager
from src.bsky_account import BskyAccount
from typing import Dict, Any
from src.newsfilter import NewsFilter
import yaml
import logging

# Config handles reading and providing access to configuration settings from config.yml
class Config:

    def __init__(self):
        self.load_configs()
        self.logger = self.__create_logger()
        self.__bsky_account = None
        self.db = DatabaseManager()
        self.news_filter = NewsFilter(self)
        self.summarizer = Summarizer(self)

    def get_summarizer(self) -> Summarizer:
        return self.summarizer
    
    def load_configs(self) -> None:
        self.__main_config = self.read_config("config/config.yml")
        self.__feed_config = self.read_config("config/feeds.yml")
        self.__filter_config = self.read_config("config/filter.yml")
        self.__tags_config = self.read_config("config/tags.yml")
        try:
            self.__session = self.read_config("config/session.yml")
        except FileNotFoundError:
            self.__session = {}

    def get_handle_password(self) -> tuple[str, str]:
        return self.__main_config['bsky_handle'], self.__main_config['bsky_password']

    def init_bsky_account(self) -> BskyAccount:
        if 'bsky_handle' not in self.__main_config or 'bsky_password' not in self.__main_config:
            self.logger.error("config.yml must contain 'bsky_handle' and 'bsky_password' keys")
            sys.exit(1)
        
        self.handle = self.__main_config['bsky_handle']
        self.password = self.__main_config['bsky_password']
        return BskyAccount(self)

    def get_admin_handle(self) -> str:
        return self.__main_config.get('admin_bsky_handle', "")

    def get_bsky_account(self) -> BskyAccount:
        if self.__bsky_account is None:
            self.__bsky_account = self.init_bsky_account()
        return self.__bsky_account

    def get_logger(self) -> logging.Logger:
        return self.logger

    def read_config(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}
        
        if not isinstance(data, dict):
            return {}
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
    
    def get_max_articles_per_feed(self) -> int:
        max_articles = self.__main_config.get("max_articles_per_feed", 10)
        if not isinstance(max_articles, int):
            raise ValueError("max_articles in config must be an integer")
        return max_articles
    
    def max_article_age_days(self) -> int:
        max_age = self.__main_config.get("max_article_age_days", None)
        if max_age is not None:
            try:
                return int(max_age)
            except ValueError:
                raise ValueError("max_article_age_days in config must be an integer")
        return 10
    
    def get_tags(self) -> Dict[str, list[str]]:
        return self.__tags_config
    
    def get_gemini_api_key(self) -> str:
        return self.__main_config.get("gemini_api_key", "")
    
    def get_gemini_model(self) -> str:
        return self.__main_config.get("gemini_model", "")
    
    def get_ai_summary_prompt(self) -> str:
        return self.__main_config.get("ai_summary_prompt", "")

    def get_delay_between_posts_seconds(self) -> int:
        return self.__main_config.get("delay_between_posts_in_seconds", 3)
    

    def save_config(self, path: str, data: Dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def get_saved_session(self) -> Dict[str, Any]:
        return self.__session if self.__session else {}
    
    def get_pds_url(self) -> str:
        return self.__main_config.get("pds_url", "https://bsky.social")

    def save_session(self) -> None:
        if self.get_bsky_account().session:
            self.__session = self.get_bsky_account().session
            self.save_config("config/session.yml", self.__session)
            # Save the updated config
            self.logger.debug("Bsky session saved to session.yml")

    def add_bad_words(self, words: list[str]) -> None:
        for word in words:
            self.__add_bad_word(word)
        self.save_config("config/filter.yml", self.__filter_config)     

    def add_good_words(self, words: list[str]) -> None:
        for word in words:
            self.__add_good_word(word)
        self.save_config("config/filter.yml", self.__filter_config)

    def __add_bad_word(self, word: str) -> None:
        self.__filter_config["bad_words"].append(word)
        self.logger.info(f"Added '{word}' to bad words filter.")

    def __add_good_word(self, word: str) -> None:
        self.__filter_config["good_words"].append(word)
        self.logger.info(f"Added '{word}' to good words filter.")

    def get_tag_keywords(self, tag: str) -> str:
        if not self.get_tags().get(tag):
            return ""
        kwds = self.get_tags()[tag]
        if kwds:
            kwd_string = "|".join(kwds)
            return kwd_string
        else:
            return ""

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