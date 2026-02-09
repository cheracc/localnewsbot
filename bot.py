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

    config.logger.info(" LocalNewsBot is starting up...")
    try:
        config.get_bsky_account().get_chat_handler().check_for_commands()
        if "--no-posts" not in __import__('sys').argv:
            fetch_filter_and_post(config)
        else:
            config.logger.info(" --no-posts flag detected, skipping fetching and posting articles.")
        config.save_session()
    except Exception as e:
        config.logger.error(f"An error occurred: {e}")
        raise
    

def fetch_filter_and_post(config: Config):
    start_time = time.time()
    # Check all RSS and HTML feeds for articles that haven't been posted
    articles = get_all_new_articles(config)
    if not articles:
        elapsed = time.time() - start_time
        config.logger.info(f" Finished({elapsed:.2f}s): No new articles found.")
        return

    # Filter articles
    total_fetched = len(articles)
    articles = config.news_filter.filter(articles)
    
    if not articles:
        elapsed = time.time() - start_time
        config.logger.info(f" Finished({elapsed:.2f}s): No articles to post after filtering.")
        return
    
    config.logger.info(f" Posting {len(articles)} articles:")
    post_all_articles(articles, config)
    elapsed = time.time() - start_time
    config.logger.info(f" Finished({elapsed:.2f}s): Fetched: {total_fetched}, Filtered: {total_fetched - len(articles)}, Posted: {len(articles)}")

def get_all_new_articles(config: Config) -> list[BskyPost]:
        start_time = time.time()
        config.logger.info(" LocalNewsBot is checking for new articles...")
        articles = src.rsssource.get_rss_feeds(config)
        articles.extend(src.htmlsource.get_html_sources(config))
        if not articles:
            return []
        config.logger.info(f" Fetched {len(articles)} articles in {time.time() - start_time:.2f} seconds.")
        return articles

def post_all_articles(articles: list[BskyPost], config: Config):
    for i, article in enumerate(articles):
        if not config.db.has_posted_article(article.link):
            # After posting, record the article as posted
            article.post_to_bluesky()
            config.db.record_posted_article(article.link)

            if i < len(articles) - 1:
                delay = config.get_delay_between_posts_seconds()
                config.logger.info(f"   Waiting {delay} seconds before next post..")
                time.sleep(delay)

if __name__ == "__main__":
    main()
