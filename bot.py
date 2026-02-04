#!/usr/bin/env python3
import datetime
import logging
import os
import socket
import time
from data import DatabaseManager

from bsky_auth import BskyAccount
from bsky_api_handler import BskyApiHandler
from config import Config
import htmlsource
from newsfilter import NewsFilter
import rsssource

# Main function
def main():
    config = Config()
    logger = __create_logger(config)
    logger.debug("config.yml loaded, Logger created with level: %s", config.get_log_level())
    
	# bail on connections if we don't have anything in 20 seconds
    socket.setdefaulttimeout(20)
    
    try:
        bsky_api_handler = BskyApiHandler(logger)
        bsky_account = BskyAccount(config, bsky_api_handler)
        logger.debug("BskyAccount %s connected and initialized", bsky_account.handle)
        
        db = DatabaseManager()
        logger.debug("DatabaseManager initialized and connected to database")
        
        filter = NewsFilter(db, config, logger)

        articles = rsssource.get_rss_feeds(config, logger, db)
        articles.extend(htmlsource.get_html_sources(config, logger))

        if not articles:
            logger.info("No new articles found from RSS or HTML sources.")
            return

        articles = filter.filter(articles)
        
        if not articles:
            logger.info("No articles to post after filtering.")
            return
        
        for article in articles:
            if not db.has_posted_article(article.link):
                logger.info(f"Posting article: {article.headline}")
            
                # After posting, record the article as posted
                bsky_account.post_article(article)
                db.record_posted_article(article.link)
                time.sleep(2)
    except Exception as e:
        logger.exception("An error occurred in main()")
        raise

def __create_logger(config: Config) -> logging.Logger:
    logger = logging.getLogger("bot")

    log_level_str = config.get_log_level().upper()
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

if __name__ == "__main__":
    main()
