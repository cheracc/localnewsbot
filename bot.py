#!/usr/bin/env python3
import datetime
import time
from data import DatabaseManager

from bsky_auth import BskyAccount
from config import Config
from newsfilter import NewsFilter
from htmlsource import WebNewsSource
from rsssource import PostableArticle, RSS_Source

# Main function
def main():
	config = Config()
	bsky_account = BskyAccount(config)
	db = DatabaseManager()
	filter = NewsFilter(db, config)

	articles = parse_rss_feeds(config)
	articles.extend(parse_html_sources(config))

	articles = filter.filter(articles)
	
	if not articles:
		print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] No articles to post after filtering.")
		return
	
	for article in articles:
		if not db.has_posted_article(article.link):
			
			print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] Posting article: {article.headline}")
		
			# After posting, record the article as posted
			bsky_account.post_article(article)
			db.record_posted_article(article.link)
			time.sleep(2)

# Parse RSS feeds from config and return list of PostableArticle
def parse_rss_feeds(config: Config) -> list[PostableArticle]:
	feeds = []
	rss_feeds = config.get_rss_feeds()
	for _, feed_info in rss_feeds.items():
		feeds.append(RSS_Source(feed_info["name"], feed_info["url"], feed_info["tag"]))

	articles = []

	for feed in feeds:
		feed_articles = feed.get_articles()

		# keep only the first x articles
		if feed_articles:
			feed_articles = feed_articles[:config.max_articles_per_feed]

		articles.extend(feed_articles)
		print(f"Fetched {len(feed_articles)} articles from RSS feed: {feed._name}")

	return articles

# Parse HTML sources from config and return list of PostableArticle
def parse_html_sources(config: Config) -> list[PostableArticle]:
	sources = []
	html_sources = config.get_html_sources()
	for _, source_info in html_sources.items():
		sources.append(WebNewsSource(source_info["name"], source_info["url"], source_info["tag"]))

	articles = []

	for source in sources:
		source_articles = source.get_articles()

		# keep only the first x articles
		if source_articles:
			source_articles = source_articles[:config.max_articles_per_feed]

		articles.extend(source_articles)
		print(f"Fetched {len(source_articles)} articles from HTML source: {source._name}")

	return articles

if __name__ == "__main__":
	main()
