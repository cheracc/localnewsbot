from __future__ import annotations
import feedparser
import datetime
import logging

from src.bsky_post import BskyPost
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.config import Config
    from feedparser import FeedParserDict

# RSS_Source handles parsing news articles from RSS feeds
class RSS_Source():
    def __init__(self, name: str, url: str, tag: str, config: Config):
        self._name = name
        self._url = url
        self._tag = tag
        self._db = config.db
        self._config = config

    def get_articles(self, max_age: int) -> list[BskyPost]:
        return self.parse_rss(max_age)

    def parse_rss(self, max_age: int) -> list[BskyPost]:
        try:
            feed = feedparser.parse(self._url)
        except Exception:
            logging.exception(f"Failed to parse RSS feed {self._name}")
            return []

        articles: list[BskyPost] = []
        if not feed.entries or not isinstance(feed.entries, list):
            return []
        
        from feedparser import FeedParserDict
        for entry in feed.entries:
            if not entry or not isinstance(entry, FeedParserDict):
                continue

            link = str(entry.link)
            if self._db.has_posted_article(link) or self._db.is_excluded(link):
                continue

            # skip if article older than configured max age

            if max_age is not None and max_age > 0:
                published_dt = None
                if getattr(entry, "published_parsed", None):
                    published_dt = datetime.datetime(*entry.published_parsed[:6]) # type: ignore
                elif getattr(entry, "published", None):
                    try:
                        published_dt = datetime.datetime.fromisoformat(str(entry.published))
                    except Exception:
                        try:
                            published_dt = datetime.datetime.strptime(str(entry.published), "%a, %d %b %Y %H:%M:%S %Z")
                        except Exception:
                            published_dt = None

                if published_dt:
                    if (datetime.datetime.now() - published_dt) > datetime.timedelta(days=int(max_age)):
                        continue

            img_url = ""
            if entry.get("enclosures") and len(entry.enclosures) > 0:
                enc_url = entry.enclosures[0]
                if any(ext in str(enc_url).lower() for ext in ["jpg", "jpeg", "png", "gif"]):
                    img_url = enc_url

            article = BskyPost(
                source_name=self._name,
                headline=str(entry.title),
                description=str(entry.description),
                link=str(entry.link),
                img_url=str(img_url),
                created_at=str(entry.published) if entry.published else datetime.datetime.now().isoformat(),
                tag=self._tag,
                config = self._config
            )
            articles.append(article)
        return articles
    
# Parse RSS feeds from config and return list of PostableArticle
def get_rss_feeds(config: Config) -> list[BskyPost]: # type: ignore
    # from src.config import Config # This import is not needed here due to the type hint 'Config'

    feeds = []
    rss_feeds = config.get_rss_feeds()
    for _, feed_info in rss_feeds.items():
        feeds.append(RSS_Source(feed_info["name"], feed_info["url"], feed_info["tag"], config))

    articles = []

    for feed in feeds:
        feed_articles = feed.get_articles(config.max_article_age_days())

        # keep only the first x articles
        if feed_articles:
            feed_articles = feed_articles[:config.get_max_articles_per_feed()]

        articles.extend(feed_articles)
        config.logger.info(f"Fetched {len(feed_articles)} articles from RSS feed: {feed._name}")

    return articles
