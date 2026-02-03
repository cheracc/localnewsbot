import feedparser

from config import Config
from postablearticle import PostableArticle

# RSS_Source handles parsing news articles from RSS feeds
class RSS_Source():
    def __init__(self, name: str, url: str, tag: str):
        self._name = name
        self._url = url
        self._tag = tag

    def get_articles(self) -> list[PostableArticle]:
        return self.parse_rss()

    def parse_rss(self) -> list[PostableArticle]:
        feed = feedparser.parse(self._url)
        articles = []
        for entry in feed.entries:
            article = PostableArticle(
                source_name=self._name,
                headline=entry.title,
                description=entry.description,
                link=entry.link,
                created_at=entry.published
            )
            articles.append(article)
        return articles
    
# Parse RSS feeds from config and return list of PostableArticle
def get_rss_feeds(config: Config) -> list[PostableArticle]:
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

