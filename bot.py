#!/usr/bin/env python3
import datetime
import logging
import os
import socket
import time
from src.data import DatabaseManager

from src.bsky_auth import BskyAccount
from src.bsky_api_handler import BskyApiHandler
from src.config import Config
from src.newsfilter import NewsFilter

import src.htmlsource
from src.newsfilter import NewsFilter
import src.rsssource

# Main function
def main():
    config = Config()
    logger = config.get_logger()
    logger.debug("config.yml loaded, Logger created with level: %s", config.get_log_level())
    
	# bail on connections if we don't have anything in 20 seconds
    socket.setdefaulttimeout(20)
    
    try:
        db = DatabaseManager()
        logger.debug("DatabaseManager initialized and connected to database")
        
        filter = NewsFilter(db, config, logger)

        articles = src.rsssource.get_rss_feeds(config, logger, db)
        articles.extend(src.htmlsource.get_html_sources(config, logger))

        if not articles:
            logger.info("No new articles found from RSS or HTML sources.")
            return

        articles = filter.filter(articles)
        
        if not articles:
            logger.info("No articles to post after filtering.")
            return
        
        bsky_api_handler = BskyApiHandler(logger)
        bsky_account = BskyAccount(config, bsky_api_handler)
        logger.debug("BskyAccount %s connected and initialized", bsky_account.handle)
        
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


if __name__ == "__main__":
    main()
