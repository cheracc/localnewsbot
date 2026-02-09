import datetime
import os
import sys

from src.aisummary import Summarizer
from src.data import DatabaseManager
from src.bsky_account import BskyAccount
from typing import Dict, Any
from src.newsfilter import NewsFilter
from src.keywordfilter import KeywordFilter
from src.aifilter import AIFilter
import yaml
import logging

# Config handles reading and providing access to configuration settings from config.yml
class Config:

    def __init__(self):
        self.load_configs()
        self.logger = self.__create_logger()
        self.__bsky_account = None
        self.db = DatabaseManager()
        self.news_filter = self._initialize_filter()
        self.summarizer = None

    def get_summarizer(self) -> Summarizer:
        if self.summarizer is None:
            self.summarizer = Summarizer(self)
        return self.summarizer
    
    def _initialize_filter(self) -> NewsFilter:
        """Initialize the appropriate filter based on config setting."""
        filter_type = self.__main_config.get("filter_type", "keyword").lower()
        
        if filter_type == "ai":
            self.logger.info("Using AI-based news filter")
            return AIFilter(self)
        else:
            self.logger.info("Using keyword-based news filter")
            return KeywordFilter(self)
    
    def get_ai_filter_quality_threshold(self) -> float:
        """Get the quality threshold for AI filter (0.0-1.0)."""
        threshold = self.__main_config.get("ai_filter_quality_threshold", 0.6)
        try:
            value = float(threshold)
            return max(0.0, min(1.0, value))  # Clamp to 0-1
        except (ValueError, TypeError):
            return 0.6
    
    def load_configs(self) -> None:
        self.__main_config = self.read_config("config/config.yml")
        self.__feed_config = self.read_config("config/feeds.yml")
        self.__filter_config: dict[str, list[str]] = self.read_config("config/filter.yml")
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
    
    # Returns the default image URL for a given feed source name
    def get_default_image_for_source(self, source_name: str) -> str:
        # Check RSS feeds
        rss_feeds = self.get_rss_feeds()
        for feed_key, feed_data in rss_feeds.items():
            if feed_data.get('name') == source_name:
                return feed_data.get('defaultimage', '')
        
        # Check HTML sources
        html_sources = self.get_html_sources()
        for source_key, source_data in html_sources.items():
            if source_data.get('name') == source_name:
                return source_data.get('defaultimage', '')
        
        return ''
    
    def get_super_bad_words(self) -> list[str]:
        super_bad_words = self.__filter_config.get("super_bad_words", []) or []
        if not isinstance(super_bad_words, list):
            raise ValueError("super_bad_words in config must be a list")
        return super_bad_words

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
    
    def get_tag_keywords(self, tag: str) -> str:
        if not self.get_tags().get(tag):
            return ""
        kwds = self.get_tags()[tag]
        if kwds:
            kwd_string = "|".join(kwds)
            return kwd_string
        else:
            return ""

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
            self.logger.debug(f"Saved updated config to {path}")

    def get_saved_session(self) -> str:
        return self.__session["session_string"] if self.__session else ""
    
    def get_pds_url(self) -> str:
        return self.__main_config.get("pds_url", "https://bsky.social")

    def save_session(self) -> None:
        session_string = self.get_bsky_account().session_string
        self.__session = {"session_string": session_string}
        self.save_config("config/session.yml", self.__session)

    def add_super_bad_words(self, words: list[str]) -> None:
        for word in words:
            self.__add_super_bad_word(word)
        self.save_config("config/filter.yml", self.__filter_config)

    def add_bad_words(self, words: list[str]) -> None:
        for word in words:
            self.__add_bad_word(word)
        self.save_config("config/filter.yml", self.__filter_config)     

    def add_good_words(self, words: list[str]) -> None:
        for word in words:
            self.__add_good_word(word)
        self.save_config("config/filter.yml", self.__filter_config)

    def remove_super_bad_words(self, words: list[str]) -> int:
        found = 0
        for word in words:
            if self.__remove_super_bad_word(word):
                found += 1
        self.save_config("config/filter.yml", self.__filter_config)
        return found

    def remove_bad_words(self, words: list[str]) -> int:
        found = 0
        for word in words:
            if self.__remove_bad_word(word):
                found += 1
        self.save_config("config/filter.yml", self.__filter_config) 
        return found

    def remove_good_words(self, words: list[str]) -> int:
        found = 0
        for word in words:
            if self.__remove_good_word(word):
                found += 1
        self.save_config("config/filter.yml", self.__filter_config) 
        return found
    
    def add_keywords_to_tag(self, tag: str, keywords: list[str]) -> bool:
        created = False
        for kw in keywords:
            if self.__add_keyword_to_tag(tag, kw):
                created = True
        self.save_config("config/tags.yml", self.__tags_config)
        return created
    
    def remove_keywords_from_tag(self, tag: str, keywords: list[str]) -> int:   
        found = 0
        for kw in keywords:
            if self.__remove_keyword_from_tag(tag, kw):
                found += 1
        self.save_config("config/tags.yml", self.__tags_config)
        return found
    
    def get_prompt(self) -> str:
        return self.__main_config.get("ai_summary_prompt", "")
    
    def save_new_prompt(self, prompt: str) -> None:
        self.__main_config["ai_summary_prompt"] = prompt
        self.save_config("config/config.yml", self.__main_config)
    
    def __add_keyword_to_tag(self, tag: str, keyword: str) -> bool:
        created = False
        if tag not in self.__tags_config:
            self.__tags_config[tag] = []
            created = True
        self.__tags_config[tag].append(keyword)
        return created
    
    def __remove_keyword_from_tag(self, tag: str, keyword: str) -> bool:
        if tag not in self.__tags_config:
            return False
        keywords = [kw for kw in self.__tags_config[tag] if kw.lower() != keyword.lower()]
        orig_len = len(self.__tags_config[tag])
        self.__tags_config[tag] = keywords
        return orig_len > len(keywords)

    def __remove_super_bad_word(self, word: str) -> bool:
        if "super_bad_words" not in self.__filter_config:
            return False
        super_badwords = [sbw for sbw in self.__filter_config["super_bad_words"] if sbw.lower() != word.lower()]
        orig_len = len(self.__filter_config["super_bad_words"])
        self.__filter_config["super_bad_words"] = super_badwords
        return orig_len > len(super_badwords)

    def __remove_bad_word(self, word: str) -> bool:
        badwords = [bw for bw in self.__filter_config["bad_words"] if bw.lower() != word.lower()]
        orig_len = len(self.__filter_config["bad_words"])
        self.__filter_config["bad_words"] = badwords
        return orig_len > len(badwords)
    
    def __remove_good_word(self, word: str) -> bool:
        goodwords = [gw for gw in self.__filter_config["good_words"] if gw.lower() != word.lower()]
        orig_len = len(self.__filter_config["good_words"])
        self.__filter_config["good_words"] = goodwords
        return orig_len > len(goodwords)

    def __add_super_bad_word(self, word: str) -> None:
        if "super_bad_words" not in self.__filter_config:
            self.__filter_config["super_bad_words"] = []
        self.__filter_config["super_bad_words"].append(word)
        self.logger.info(f" Added '{word}' to super bad words filter.")

    def __add_bad_word(self, word: str) -> None:
        self.__filter_config["bad_words"].append(word)
        self.logger.info(f" Added '{word}' to bad words filter.")

    def __add_good_word(self, word: str) -> None:
        self.__filter_config["good_words"].append(word)
        self.logger.info(f" Added '{word}' to good words filter.")

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