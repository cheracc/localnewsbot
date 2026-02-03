#!/usr/bin/env python3
import datetime
import time
from data import DatabaseManager

from bsky_auth import BskyAccount
from config import Config
from newsfilter import NewsFilter
from htmlsource import WebNewsSource
from postablearticle import PostableArticle
import rsssource

# Main function
def main():
	config = Config()
	bsky_account = BskyAccount(config)
	db = DatabaseManager()
	filter = NewsFilter(db, config)

	articles = rsssource.get_rss_feeds(config)
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
