#!/usr/bin/env python3
import socket
import time
import src.htmlsource
import src.rsssource
from src.bsky_post import BskyPost
from src.config import Config

# Main function
def main():
	# bail on connections if we don't have anything in 20 seconds
    socket.setdefaulttimeout(20)
    config = Config() # loads config files and sets up database and api
    
    # Check all RSS and HTML feeds for articles that haven't been posted
    articles = get_all_new_articles(config)
    
    if not articles:
        return

    # Filter articles
    total_fetched = len(articles)
    articles = config.news_filter.filter(articles)
    
    if not articles:
        config.logger.info("No articles to post after filtering.")
        return
    
    config.logger.info(f"Posting {len(articles)} articles.")
    post_all_articles(articles, config) 
    config.logger.info(f"Fetched {total_fetched}, filtered {total_fetched - len(articles)}, and posted {len(articles)} articles.")


def get_all_new_articles(config: Config) -> list[BskyPost]:
        start_time = time.time()
        config.logger.info("Checking for new articles...")
        articles = src.rsssource.get_rss_feeds(config)
        articles.extend(src.htmlsource.get_html_sources(config))
        if not articles:
            config.logger.info("No new articles found.")
            return []
        config.logger.info(f"Fetched {len(articles)} articles in {time.time() - start_time:.2f} seconds.")
        return articles

def post_all_articles(articles: list[BskyPost], config: Config):
    for article in articles:
        if not config.db.has_posted_article(article.link):
            config.logger.info(f"Posting article: {article.headline}")
        
            # After posting, record the article as posted
            article.post_to_bluesky()
            config.db.record_posted_article(article.link)
            time.sleep(2)
    

if __name__ == "__main__":
    main()
