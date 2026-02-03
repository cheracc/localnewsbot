#!/usr/bin/env python3
import datetime
import time
from data import DatabaseManager

from bsky_auth import BskyAccount
from config import Config
import htmlsource
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
	articles.extend(htmlsource.get_html_sources(config))

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


if __name__ == "__main__":
	main()
