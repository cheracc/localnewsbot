#!/usr/bin/env python3
import socket
import time
import src.htmlsource
import src.rsssource
from src.bskypost import BskyPost
from src.config import Config

# Main function
def main():
	# bail on connections if we don't have anything in 20 seconds
    socket.setdefaulttimeout(20)
    config = Config()
    
    # Check all RSS and HTML feeds for articles that haven't been posted
    articles = get_all_new_articles(config)
    
    if not articles:
        config.logger.info("No new articles found from RSS or HTML sources.")
        return

    # Filter articles
    articles = config.news_filter.filter(articles)
    
    if not articles:
        config.logger.info("No articles to post after filtering.")
        return
    
    post_all_articles(articles, config) 
    

def get_all_new_articles(config: Config) -> list[BskyPost]:
        articles = src.rsssource.get_rss_feeds(config)
        articles.extend(src.htmlsource.get_html_sources(config))
        return articles

def post_all_articles(articles: list[BskyPost], config: Config):
    bsky_account = config.get_bsky_account()
    
    for article in articles:
        if not config.db.has_posted_article(article.link):
            config.logger.info(f"Posting article: {article.headline}")
        
            # After posting, record the article as posted
            article.post_to_bluesky(bsky_account)
            config.db.record_posted_article(article.link)
            time.sleep(2)
    

if __name__ == "__main__":
    main()
